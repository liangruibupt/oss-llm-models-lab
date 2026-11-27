# 🛠 DeepInfer 实践：DeepSeek-V4.1-Flash 离线推理

> **checked 2026-11-27**，命令来自 [DeepInfer README](https://github.com/deepseek-ai/DeepInfer#readme) 与 [examples/README.md](https://github.com/deepseek-ai/DeepInfer/blob/main/examples/README.md)（DeepInfer@`a679bb8`），**未在本仓库实测**。

## 先看限制

- 只支持 **DeepSeek-V4.1-Flash**（默认权重 [`deepseek-ai/DeepSeek-V4.1-Flash-1017`](https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash-1017)）。
- 只开源了**离线推理**：没有 HTTP / OpenAI 兼容服务；KV cache 系统、VE/Prefill/Decode 分离、数据并行负载均衡都不在开源范围内。所以本仓库的 OpenAI 压测 harness 不能直接用，要用它自带的 `examples/benchmark.py`。
- 硬件：NVIDIA **SM100**（B200 级，CUDA 13）或华为昇腾 950（CANN 9.2）。AWS 上对应 `p6-b200.48xlarge`（8×B200）。B300 属于 SM103，README 没有写，本仓库不推断。
- 生产上的最小高效部署单元是 64 张 prefill GPU + 64 张 decode GPU（[部署 Q&A](https://github.com/deepseek-ai/DeepInfer/blob/main/doc/inference_deployment_qa.md)）。单台 8 卡只能做功能验证和单机基准，不代表线上规模的性能。

## 构建

前置：Linux、GCC ≥ 13、Python 3.12、CUDA 13。先建一个空的 Python 3.12 环境：

```bash
git clone https://github.com/deepseek-ai/DeepInfer.git && cd DeepInfer
export DEEPINFER_ACCELERATOR=nvidia   # 昇腾用 ascend；运行时也要保持这个环境变量
./build.sh
```

## 离线推理

```bash
export WORLD_SIZE=1 RANK=0
export CUDA_VISIBLE_DEVICES=0,1,2,3,4,5,6,7
# 首次运行会把权重下到 HF cache；用本地副本时设 DEEPINFER_HF_MODEL_DIR=/path/to/DeepSeek-V4.1-Flash-1017
python examples/offline_inference.py --ep 8
# 其他官方示例：
python examples/offline_inference.py --ep 2 --dp 8
python examples/offline_inference.py --ep 2 --cp 8
```

## 基准

`examples/benchmark.py` 把 prefill 和 decode 分开测，默认 `decode_num_requests=64`、`context_length=32768`、`non_cached_tokens=4096`、`prefill_batch_size=32768`、nextn=5，输出 prefill 吞吐（tokens/s/GPU）、decode avg_SPS 和 decode 吞吐（tokens/s/GPU，按全接受计算）。

```bash
export WORLD_SIZE=1 RANK=0
export CUDA_VISIBLE_DEVICES=0,1,2,3,4,5,6,7
python examples/benchmark.py --result_jsonl results/deepinfer_v41flash_p6b200.jsonl
# CP8 + 更大的 prefill chunk（README 示例）
python examples/benchmark.py --cp 8 --prefill_batch_size 65536
# 关闭投机解码做对照
DEEPINFER_USE_NEXTN_DECODE=0 python examples/benchmark.py
```

注意：decode 吞吐按「每请求每步 1+nextn 个 token」的全接受口径计算，与按真实接受率统计的在线压测结果不可直接比较。

## 常用开关（README）

| 变量 | 作用 |
|---|---|
| `DEEPINFER_ENABLE_MTP_VARLEN=1` | DSpark + 置信度调度验证；`DEEPINFER_USE_NEXTN_DECODE` 控制最大 draft 长度（默认 5） |
| `DEEPINFER_YOCO_PREFILL_TRUNCATION_MODE=compact`、`DEEPINFER_YOCO_PREFILL_KEEP_TOKENS=140` | decoder SWA bounded replay 的 V4.1 默认设置 |
| `DEEPINFER_BATCH_INVARIANT=1` | batch-invariant 推理（仅 NVIDIA） |
