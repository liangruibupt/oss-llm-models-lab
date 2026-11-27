# 🛠 TrnRT 实践：GLM-5.3-Flash on trn2.48xlarge

> **checked 2026-11-27**，命令转录自 [TrnRT README Quickstart](https://github.com/RunanywhereAI/trnrt#quickstart)（v0.2.0）与 [DEPLOY.md](https://github.com/RunanywhereAI/trnrt/blob/development/docs/DEPLOY.md)，**未在本仓库实测**。TrnRT 目前只支持这一个组合。

## 需要什么

| 角色 | 机型 | 说明 |
|---|---|---|
| 编译主机 | 任意 x86_64 + Docker，不需要 NeuronCore | 每个 `neuronx-cc` 进程默认预留 30 GB 内存，并发数由内存决定；构建编译缓存「需要数小时」。例如 `m7i.16xlarge`（256 GiB） |
| 服务主机 | `trn2.48xlarge` | 16 颗 Trainium2 × 96 GiB HBM，LNC 2；跑 2 个引擎，每个引擎 TP32 |
| 软件 | Neuron SDK 2.32（neuronx-cc 2.27）、Python 3.13，全部在 TrnRT 镜像里 | |

trn2.48xlarge 在 2026-11-27 的 AWS Price List 中没有美国区按需价，需通过 [EC2 Capacity Blocks for ML](https://aws.amazon.com/ec2/capacityblocks/) 预订，新手先读 [docs/AWS.md](https://github.com/RunanywhereAI/trnrt/blob/development/docs/AWS.md)。

## 1. 构建镜像（编译主机和服务主机都要）

```bash
git clone https://github.com/RunanywhereAI/trnrt.git && cd trnrt
docker build -f docker/Dockerfile \
  --build-arg TRNRT_VERSION=$(python3 -c 'import trnrt; print(trnrt.__version__)') \
  --build-arg TRNRT_REVISION=$(git rev-parse HEAD) -t trnrt .
```

## 2. 在编译主机上构建编译缓存（数小时）

```bash
OUT=/data/trnrt REV=eb9eb208eb0d988989d07a6a12d0fdeb5f52574a
mkdir -p $OUT/nki $OUT/work
trnrt() { docker run --rm -e HF_TOKEN -v $OUT:$OUT \
  -v $OUT/nki:/var/tmp/nki-intermediate-cache trnrt "$@"; }
trnrt compile shapes zai-org/GLM-5.3-Flash --revision $REV --out $OUT
trnrt compile decisions --model zai-org/GLM-5.3-Flash --revision $REV --out $OUT
trnrt compile capture --out $OUT -- --model $OUT/shapes
trnrt compile compile --out $OUT --work-root $OUT/work
trnrt compile strip --out $OUT
```

`strip` 不能省：在 1M token 的 bucket 下，运行时会在主机内存里保存每个 NEFF 的多份副本（DEPLOY.md）。

## 3. 在 trn2.48xlarge 上服务

把 `$OUT/cache` 和 `$OUT/nki` 拷到服务主机，然后：

```bash
hf download zai-org/GLM-5.3-Flash --revision eb9eb208eb0d988989d07a6a12d0fdeb5f52574a \
  --local-dir /models/GLM-5.3-Flash
docker run --rm --privileged --network host --ipc=host \
  -v /data/trnrt/cache:/cache \
  -v /data/trnrt/nki:/var/tmp/nki-intermediate-cache \
  -v /models/GLM-5.3-Flash:/model \
  -e NEURON_LIBTORCH_CACHE_ROOT=/cache \
  trnrt serve --model /model --port 8000
```

构建档位：默认 `balanced`；`latency`（开 MTP，每个引擎 1–8 用户）、`throughput` 按并发选，或用 `--preset auto --users N`（[CONFIGURATION.md](https://github.com/RunanywhereAI/trnrt/blob/development/docs/CONFIGURATION.md)）。每个引擎启动有 `--startup-timeout`（默认 3600 s）。

## 4. 发请求

README 示例中模型名是 `glm`，`session_id` 让同一会话固定在一个引擎上以复用前缀缓存：

```bash
curl -s http://127.0.0.1:8000/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{"model": "glm", "messages": [{"role": "user", "content": "Write a haiku about Trainium."}], "session_id": "my-session", "max_tokens": 128}'
```

## 5. 压测

```bash
python bench/llm_bench.py --base-url http://127.0.0.1:8000/v1 --model glm \
  --input-len 8192 --output-len 1024 --concurrency 1,8,32,64 \
  --label "TrnRT 0.2.0 / trn2.48xlarge / FP8 / balanced" --out results/glm53flash_trnrt_trn2
```

`--no-ignore-eos` 视情况使用：TrnRT 的 [API.md](https://github.com/RunanywhereAI/trnrt/blob/development/docs/API.md) 才是可接受参数的准绳，若服务端拒绝 `ignore_eos` / `min_tokens`，加这个开关。

## 已知限制

- README 的基准数据来自早于 v0.2.0 的内部构建；v0.2.0 的设备端运行在 README 中标为「pending」（[KNOWN_ISSUES.md](https://github.com/RunanywhereAI/trnrt/blob/development/docs/KNOWN_ISSUES.md)）。
- 只支持 GLM-5.3-Flash 与 trn2.48xlarge。
