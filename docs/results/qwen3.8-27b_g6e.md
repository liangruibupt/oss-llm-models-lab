# Qwen3.8-27B-FP8 · g6e.xlarge：vLLM vs SGLang（实测结果）

> 状态：✅ 已实测（2026-11-27）· 对应 [`../BENCH_PLAN.md`](../BENCH_PLAN.md) 的 P0 行。
> ⚠ **数据完整性**：原始 JSON、服务端日志和显存采样文件随实例一起丢失（取回文件的 `scp` 与终止脚本同时启动，实例在拷贝中途被终止）。下面的 vLLM 数据是压测工具打印的完整 markdown 表，SGLang 只有逐级摘要（输出 tok/s、TTFT p50、TPOT p50），都是从运行时的控制台输出转录的，没有改动数字。详见 [`results/qwen3.8-27b_g6e/README.md`](../../results/qwen3.8-27b_g6e/README.md)。

| 项 | 值 |
|---|---|
| 模型 | [Qwen/Qwen3.8-27B-FP8](https://huggingface.co/Qwen/Qwen3.8-27B-FP8)，revision `c3a462cc3d38cf351f3b26cbd763469eeb74ef81`（官方 block-scaled FP8，28.7 GiB） |
| 框架 | vLLM（镜像 `vllm/vllm-openai:qwen38`）+ SGLang 0.5.23（镜像 `lmsysorg/sglang:latest`），同一台实例先后跑 |
| 实例 | `g6e.xlarge`（1×NVIDIA L40S 48GB），**ap-northeast-1c**，`i-082a2f7256ae3c051` |
| 精度 | FP8 权重；SGLang 用 FP8 KV cache（cookbook 原参数），vLLM 用默认 KV dtype |
| 预估成本（BENCH_PLAN） | 3 h · $5.58 |
| **实际实例小时 / 成本** | 03:16:59 → 05:32:46 UTC = **2.26 h × $1.861 = $4.21**（另有约 $0.06 的 200 GB gp3 EBS） |
| 运行日期（UTC） | 2026-11-27 |
| 运行者 | Kiro agent（Liang 审批的 ~$6 预算） |
| 原始数据目录 | [`results/qwen3.8-27b_g6e/`](../../results/qwen3.8-27b_g6e/) |

这是**非官方硬件**组合：vLLM recipe 与 SGLang cookbook 都没有 L40S 配置，所以下面的命令以官方命令为基础，按 48 GB 显存做了必要改动（逐条列出）。

## 版本

| 项 | 值 |
|---|---|
| AMI | `ami-01431a4029b0c29de` Deep Learning Base OSS Nvidia Driver GPU AMI (Ubuntu 24.04) 20261120（SSM `/aws/service/deeplearning/ami/x86_64/base-oss-nvidia-driver-gpu-ubuntu-24.04/latest/ami-id`） |
| 驱动 / CUDA | NVIDIA 620.70.06，CUDA UMD 13.5；Docker 29.10.0 |
| vLLM | `vllm/vllm-openai:qwen38` @ `sha256:4a2f33a8…c1bc31`：vllm 0.1.dev19754+g3a0914114、torch 2.13.0+cu130、flashinfer 0.6.17、Python 3.12.3 |
| SGLang | `lmsysorg/sglang:latest` @ `sha256:f832b5c3…7f1f`：sglang 0.5.23、torch 2.14.1+cu130、flashinfer 0.7.2、Python 3.12.16 |
| 峰值显存（nvidia-smi，2 s 采样） | vLLM 40,363 MiB；SGLang 44,297 MiB |

选这个 AMI 的原因：两个框架镜像都是 CUDA 13.0 构建，需要新驱动；image 仓库用的 PyTorch 2.7 DLAMI（Ubuntu 22.04）驱动偏旧。

## 流程与脚本

| 步骤 | 命令 / 脚本 |
|---|---|
| 开机 | `python scripts/launch.py --name oss-llm-bench-qwen27b`（boto3；自有 Name tag、key pair、SG，SSH 只放行本机 IP；key 存 `~/.oss-llm-bench/`） |
| 准备 | 实例上 `bash scripts/box/setup_qwen27b.sh`：并行拉两个镜像，下载 FP8 权重，记录版本 |
| 压测 | 实例上 `bash scripts/box/bench_qwen27b.sh vllm` / `sglang`：起容器 → 等 `/v1/models` → W1 → W2 → 停容器；后台每 2 s 采样显存 |
| 关机 | `python scripts/teardown.py --name oss-llm-bench-qwen27b`（核对 Name tag 后才终止）；另设 `shutdown -h +120` 兜底 |

### vLLM 启动命令

基于 [vLLM recipe](https://recipes.vllm.ai/Qwen/Qwen3.8-27B)（`fp8` 变体，单卡 TP1）：

```bash
docker run -d --name srv --gpus all --ipc=host -p 8000:8000 \
  -v $HOME/hf:/root/.cache/huggingface -v $HOME/vllm-cache:/root/.cache/vllm \
  -e HF_HUB_OFFLINE=1 -e VLLM_USE_RUST_FRONTEND=0 \
  vllm/vllm-openai:qwen38 Qwen/Qwen3.8-27B-FP8 \
    --tensor-parallel-size 1 \
    --enable-auto-tool-choice --tool-call-parser qwen3_coder --reasoning-parser qwen3 \
    --language-model-only \
    --max-model-len 16384 --gpu-memory-utilization 0.92 --max-num-seqs 64
```

相对 recipe 的改动：
- `VLLM_USE_RUST_FRONTEND=0`（recipe 为 1）：Rust 前端渲染 checkpoint 的 chat template 失败，报 `unknown statement generation`，引擎起不来。
- `--max-num-seqs 64`：默认 256 时报 `max_num_seqs (256) exceeds available Mamba cache blocks (199)`。
- `--language-model-only`（recipe 的 `text_only` 可选项）、`--max-model-len 16384`、`--gpu-memory-utilization 0.92`：为 48 GB 腾出 KV cache。启动日志显示可用 KV 10.09 GiB，即 127,431 token，16K 上下文下最多同时容纳 7.78 个请求。

### SGLang 启动命令

基于 [SGLang cookbook](https://docs.sglang.io/cookbook/autoregressive/Qwen/Qwen3.8-27B) 的 H200 FP8 `high-throughput` 命令：

```bash
docker run -d --name srv --gpus all --ipc=host --shm-size 32g -p 30000:30000 \
  -v $HOME/hf:/root/.cache/huggingface -e HF_HUB_OFFLINE=1 \
  lmsysorg/sglang:latest sglang serve \
    --trust-remote-code --model-path Qwen/Qwen3.8-27B-FP8 \
    --kv-cache-dtype fp8_e4m3 --mem-fraction-static 0.88 --attention-backend flashinfer \
    --chunked-prefill-size 8192 --max-prefill-tokens 8192 --cuda-graph-backend-prefill disabled \
    --reasoning-parser qwen3 --tool-call-parser qwen3_coder \
    --host 0.0.0.0 --port 30000 \
    --mamba-ssm-dtype float32 --max-running-requests 32 --disable-radix-cache \
    --context-length 16384
```

按顺序尝试过的改动：
1. 原样的 cookbook 参数（`--mem-fraction-static 0.85`、chunked/max prefill 32768）：捕获 prefill CUDA graph 时 OOM。
2. 改为 0.80、chunked/max prefill 8192、关闭 prefill CUDA graph、去掉 `--mamba-radix-cache-strategy extra_buffer_lazy`：能启动，但日志显示 mamba 状态缓存把 `max_running_requests` 限到 **4**（每个请求占 5 个状态槽）。为了公平比较，中止这一次。
3. 加 `--disable-radix-cache`（每个请求只占 1 个 mamba 状态；本压测没有前缀复用）、`--max-running-requests 64`、0.85：权重加载后没有空间留给 KV cache，报错退出。
4. **最终**：`--max-running-requests 32`、`--mem-fraction-static 0.88`。mamba 状态 4.64 GB，KV cache 174,882 token（FP8）。

## 压测命令

客户端在同一台实例上，走 127.0.0.1。`<PORT>` 为 8000（vLLM）或 30000（SGLang）。

```bash
# W1：1024 输入 / 256 输出，每级 4×并发个请求（最少 16），2 个预热
python3 bench/llm_bench.py --base-url http://127.0.0.1:<PORT>/v1 --model Qwen/Qwen3.8-27B-FP8 \
  --input-len 1024 --output-len 256 --concurrency 1,8,32,64 --requests-per-concurrency 4 \
  --out results/qwen3.8-27b_g6e/<fw>/w1_1024_256
# W2：8192 输入 / 1024 输出，每级 1×并发个请求（最少 8），2 个预热
python3 bench/llm_bench.py --base-url http://127.0.0.1:<PORT>/v1 --model Qwen/Qwen3.8-27B-FP8 \
  --input-len 8192 --output-len 1024 --concurrency 1,8,32,64 --requests-per-concurrency 1 --min-requests 8 \
  --out results/qwen3.8-27b_g6e/<fw>/w2_8192_1024
```

为了守住 3 个实例小时的上限，W2 的请求数从计划的「4×并发」降到了「1×并发，最少 8」。服务端按 chat template 计数，实际输入长度是 1076 / 8244 token。默认开着 thinking，输出 token 里包含 reasoning 内容（压测工具会把 `reasoning_content` 一并计入）。

## 结果

TTFT / TPOT 单位 ms。SGLang 的 p99 与请求/s 随原始文件丢失，记为「-」。

| 负载 | 并发 | 框架 | 成功/总数 | TTFT p50 | TTFT p99 | TPOT p50 | TPOT p99 | 输出 tok/s | 请求/s |
|---|---:|---|---:|---:|---:|---:|---:|---:|---:|
| W1 1024/256 | 1 | vLLM | 16/16 | 268.2 | 274.2 | 59.97 | 59.99 | 16.5 | 0.06 |
| W1 1024/256 | 1 | SGLang | 16/16 | 250.6 | - | 53.57 | - | 18.4 | - |
| W1 1024/256 | 8 | vLLM | 32/32 | 1,160.1 | 1,924.3 | 55.24 | 57.31 | 134.9 | 0.53 |
| W1 1024/256 | 8 | SGLang | 32/32 | 2,118.1 | - | 49.87 | - | 136.5 | - |
| W1 1024/256 | 32 | vLLM | 128/128 | 1,601.4 | 7,442.4 | 89.31 | 91.94 | 335.2 | 1.31 |
| W1 1024/256 | 32 | SGLang | 128/128 | 6,652.7 | - | 72.75 | - | 327.5 | - |
| W1 1024/256 | 64 | vLLM | 256/256 | 9,607.8 | 32,683.5 | 102.30 | 106.02 | **361.3** | 1.41 |
| W1 1024/256 | 64 | SGLang | 256/256 | 29,679.7 | - | 69.67 | - | 332.9 | - |
| W2 8192/1024 | 1 | vLLM | 8/8 | 1,917.9 | 1,981.2 | 60.66 | 60.66 | 16.1 | 0.02 |
| W2 8192/1024 | 1 | SGLang | 8/8 | 2,158.2 | - | 54.02 | - | 17.8 | - |
| W2 8192/1024 | 8 | vLLM | 8/8 | 5,693.5 | 12,144.5 | 64.38 | 68.83 | 112.9 | 0.11 |
| W2 8192/1024 | 8 | SGLang | 8/8 | 12,141.0 | - | 57.08 | - | 116.1 | - |
| W2 8192/1024 | 32 | vLLM | 32/32 | 109,388.7 | 240,046.5 | 70.32 | 97.97 | 109.0 | 0.11 |
| W2 8192/1024 | 32 | SGLang | 32/32 | 38,368.1 | - | 73.36 | - | 169.8 | - |
| W2 8192/1024 | 64 | vLLM | 64/64 | 259,333.0 | 538,117.0 | 70.63 | 85.75 | 109.3 | 0.11 |
| W2 8192/1024 | 64 | SGLang | 64/64 | 136,222.1 | - | 74.06 | - | **170.1** | - |

全部 1,088 个请求（每个框架 544 个）都成功。

## 结论

1. **单卡 L40S 能跑 Qwen3.8-27B-FP8**，但两个框架都要改官方参数才能启动（见上），而且单流只有 16–18 tok/s（TPOT 54–60 ms）。两个框架都提示找不到 L40S 的 W8A8 block-FP8 GEMM 调优配置、退回默认配置，这可能是单流偏慢的原因之一（未验证）。
2. **短输入（W1）**：低并发下 SGLang 单流更快（TPOT 53.6 对 60.0 ms，约快 11%）；并发 32/64 时 vLLM 吞吐略高（361 对 333 tok/s），首 token 也短得多（c=64 时 TTFT p50 9.6 s 对 29.7 s），因为 SGLang 被限在 32 个并发请求，其余请求在排队。
3. **长输入（W2）**：瓶颈是 KV 与线性注意力状态的容量。vLLM 的 KV 只够同时放下约 8 个 16K 请求，从并发 8 起吞吐就停在约 109 tok/s；SGLang 用 FP8 KV（174,882 token）和 32 个并发槽，c=32/64 时达到约 170 tok/s（高约 56%），TTFT p50 也更短。这里的差异主要来自 KV dtype 和并发上限的设置，不能简单理解为框架本身快慢。
4. 用这台机器做长上下文、高并发服务不划算；48 GB 卡上更适合低并发或短上下文。要做公平的引擎对比，下一步应让两边 KV dtype 和最大并发一致（例如 vLLM 加 `--kv-cache-dtype fp8`），或者换用显存更大的卡。

## 实际成本与时间线（UTC）

| 时间 | 事件 |
|---|---|
| 03:16:59 | 开机（ap-northeast-1a 无容量，1c 成功） |
| 03:19–03:28 | 拉镜像（4.5 min）、下载权重（约 1.5 min）、记录版本 |
| 03:29–03:51 | vLLM 4 次启动失败：HF 离线模式缺 `refs/main`、Rust 前端 chat template、`max_num_seqs`、脚本被覆盖导致的残留进程 |
| 03:57–04:38 | vLLM 就绪并完成 W1 + W2 |
| 04:38–04:58 | SGLang 3 次失败 / 中止（见上），第 4 次就绪 |
| 04:58–05:32 | SGLang 完成 W1 + W2 |
| 05:32:46 | 终止，`describe-instances` 确认 `terminated` |

**实例小时 2.26 h，按需 $1.861/h，合计 $4.21**，在审批的约 $6 / 3 小时上限内。
