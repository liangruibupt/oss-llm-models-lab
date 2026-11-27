# 🛠 SGLang 实践：在 AWS 上启动矩阵中的 ✅ 组合

> **checked 2026-11-27**，命令取自 SGLang cookbook 生成的命令文件（`python/sglang/cli/_commands/*.json`，sglang@`f8fd250`），只做了 AWS 机型映射，**未在本仓库实测**。cookbook 给每条命令标了状态：`verified`（SGLang 团队实测过）、`in-progress`、`unverified`，下面原样保留。实测计划见 [`../BENCH_PLAN.md`](../BENCH_PLAN.md)。

## AWS 机型映射

| cookbook 硬件 | AWS 实例 | 说明 |
|---|---|---|
| H100 ×8 | `p5.48xlarge` | 8×H100 80GB |
| H200 ×8 | `p5en.48xlarge` / `p5e.48xlarge` | 8×H200 141GB |
| B200 ×8 | `p6-b200.48xlarge` | 8×B200 |
| B300 ×8 | `p6-b300.48xlarge` | 8×B300 |
| GB200 / GB300 | `p6e-gb200` / `p6e-gb300` UltraServer | 机架级，本仓库不展开 |

价格见 [`../BENCH_PLAN.md`](../BENCH_PLAN.md#价格来源)。

## 通用步骤

1. 选 AWS Deep Learning AMI（NVIDIA 驱动 + Docker + NVIDIA Container Toolkit），实例上挂足够大的 NVMe / EBS 存权重（1T 级模型的 FP8 权重约 1 TB）。
2. 启动容器（[SGLang 安装文档 Method 3](https://docs.sglang.io/docs/get-started/install)），再在容器里执行下面的 `sglang serve ...`：

```bash
HF_CACHE_DIR=/opt/dlami/nvme/hf-cache
docker run -it --gpus all --shm-size 32g -p 30000:30000 \
  -v "$HF_CACHE_DIR:/root/.cache/huggingface" --ipc=host \
  -e HF_TOKEN \
  lmsysorg/sglang:latest bash
```

镜像例外：Mistral Large 4 用 `lmsysorg/sglang:mistral-large-4`；Kimi K3.1 Pro 用 `lmsysorg/sglang:dev-kimi-k31-pro`（cookbook 原文说明）。

3. 用 OpenAI 兼容接口发一个请求：

```bash
MODEL=zai-org/GLM-5.3-Flash   # 与 --model-path 相同
curl -s http://127.0.0.1:30000/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{"model": "'"$MODEL"'", "messages": [{"role": "user", "content": "用一句话介绍你自己"}], "max_tokens": 128}'
```

4. 压测：`python bench/llm_bench.py --base-url http://127.0.0.1:30000/v1 --model <served-model-name> ...`（见 [`../../bench/README.md`](../../bench/README.md)）。

5. 用完立刻停止或终止实例。

## 各模型启动命令

### DeepSeek-V4.1-Flash（`deepseek-ai/DeepSeek-V4.1-Flash-1017`）

来源：[SGLang cookbook](https://docs.sglang.io/cookbook/autoregressive/DeepSeek/DeepSeek-V4_1)。下面每种机型只列一条（优先 cookbook 标为 verified 的），其余策略见 cookbook 页面。

**p5en.48xlarge / p5e.48xlarge（8×H200 141GB） · 策略 `high-throughput` · cookbook 状态：unverified** · [cookbook 原始配置](https://docs.sglang.io/cookbook/autoregressive/DeepSeek/DeepSeek-V4_1#hw=h200&variant=flash-1017&quant=fp4&strategy=high-throughput&nodes=single)

```bash
sglang serve \
  --trust-remote-code \
  --model-path deepseek-ai/DeepSeek-V4.1-Flash-1017 \
  --tp 8 \
  --ep-size 8 \
  --mem-fraction-static 0.8 \
  --attention-backend dsv4 \
  --moe-runner-backend flashinfer_mxfp4 \
  --max-running-requests 256 \
  --cuda-graph-max-bs-decode 64 \
  --reasoning-parser auto \
  --tool-call-parser auto \
  --host 0.0.0.0 \
  --port 30000
```

**p6-b200.48xlarge（8×B200） · 策略 `high-throughput` · cookbook 状态：unverified** · [cookbook 原始配置](https://docs.sglang.io/cookbook/autoregressive/DeepSeek/DeepSeek-V4_1#hw=b200&variant=flash-1017&quant=fp4&strategy=high-throughput&nodes=single)

```bash
sglang serve \
  --trust-remote-code \
  --model-path deepseek-ai/DeepSeek-V4.1-Flash-1017 \
  --tp 4 \
  --ep-size 4 \
  --max-running-requests 256 \
  --reasoning-parser auto \
  --tool-call-parser auto \
  --host 0.0.0.0 \
  --port 30000
```

**p6-b300.48xlarge（8×B300） · 策略 `high-throughput` · cookbook 状态：unverified** · [cookbook 原始配置](https://docs.sglang.io/cookbook/autoregressive/DeepSeek/DeepSeek-V4_1#hw=b300&variant=flash-1017&quant=fp4&strategy=high-throughput&nodes=single)

```bash
sglang serve \
  --trust-remote-code \
  --model-path deepseek-ai/DeepSeek-V4.1-Flash-1017 \
  --tp 4 \
  --ep-size 4 \
  --max-running-requests 256 \
  --reasoning-parser auto \
  --tool-call-parser auto \
  --host 0.0.0.0 \
  --port 30000
```

### DeepSeek-V4-Pro-0813（`deepseek-ai/DeepSeek-V4-Pro-0813`）

来源：[SGLang cookbook](https://docs.sglang.io/cookbook/autoregressive/DeepSeek/DeepSeek-V4)。下面每种机型只列一条（优先 cookbook 标为 verified 的），其余策略见 cookbook 页面。

**p5en.48xlarge / p5e.48xlarge（8×H200 141GB） · 策略 `balanced` · cookbook 状态：unverified** · [cookbook 原始配置](https://docs.sglang.io/cookbook/autoregressive/DeepSeek/DeepSeek-V4#hw=h200&variant=pro-official&quant=fp4&strategy=balanced&nodes=single&pdMode=prefill)

```bash
sglang serve \
  --trust-remote-code \
  --model-path deepseek-ai/DeepSeek-V4-Pro-0813 \
  --tp 8 \
  --moe-runner-backend flashinfer_mxfp4 \
  --speculative-algorithm DSPARK \
  --mem-fraction-static 0.88 \
  --host 0.0.0.0 \
  --port 30000
```

**p6-b200.48xlarge（8×B200） · 策略 `balanced` · cookbook 状态：unverified** · [cookbook 原始配置](https://docs.sglang.io/cookbook/autoregressive/DeepSeek/DeepSeek-V4#hw=b200&variant=pro-official&quant=fp4&strategy=balanced&nodes=single&pdMode=prefill)

```bash
export SGLANG_OPT_DEEPGEMM_MEGA_MOE_NUM_MAX_TOKENS_PER_RANK=4096 SGLANG_OPT_USE_TOPK_V2=1
SGLANG_OPT_DEEPGEMM_MEGA_MOE_NUM_MAX_TOKENS_PER_RANK=4096 \
SGLANG_OPT_USE_TOPK_V2=1 \
sglang serve \
  --trust-remote-code \
  --model-path deepseek-ai/DeepSeek-V4-Pro-0813 \
  --tp 8 \
  --attn-dp-size 8 \
  --moe-a2a-backend megamoe \
  --chunked-prefill-size 32768 \
  --swa-full-tokens-ratio 0.1 \
  --mem-fraction-static 0.92 \
  --cuda-graph-max-bs-decode 256 \
  --host 0.0.0.0 \
  --port 30000
```

**p6-b300.48xlarge（8×B300） · 策略 `balanced` · cookbook 状态：unverified** · [cookbook 原始配置](https://docs.sglang.io/cookbook/autoregressive/DeepSeek/DeepSeek-V4#hw=b300&variant=pro-official&quant=fp4&strategy=balanced&nodes=single&pdMode=prefill)

```bash
sglang serve \
  --trust-remote-code \
  --model-path deepseek-ai/DeepSeek-V4-Pro-0813 \
  --tp 8 \
  --attn-dp-size 8 \
  --moe-runner-backend flashinfer_mxfp4 \
  --disable-flashinfer-autotune \
  --chunked-prefill-size 32768 \
  --swa-full-tokens-ratio 0.1 \
  --mem-fraction-static 0.92 \
  --cuda-graph-max-bs-decode 256 \
  --deepep-config '{"normal_dispatch":{"num_sms":96},"normal_combine":{"num_sms":96}}' \
  --host 0.0.0.0 \
  --port 30000
```

### DeepSeek-V4-Pro-0813-NVFP4（`nvidia/DeepSeek-V4-Pro-0813-NVFP4`）

来源：[SGLang cookbook](https://docs.sglang.io/cookbook/autoregressive/DeepSeek/DeepSeek-V4)。下面每种机型只列一条（优先 cookbook 标为 verified 的），其余策略见 cookbook 页面。

**p6-b200.48xlarge（8×B200） · 策略 `low-latency` · cookbook 状态：verified** · [cookbook 原始配置](https://docs.sglang.io/cookbook/autoregressive/DeepSeek/DeepSeek-V4#hw=b200&variant=pro-official&quant=nvfp4&strategy=low-latency&nodes=single&pdMode=prefill)

```bash
sglang serve \
  --trust-remote-code \
  --model-path nvidia/DeepSeek-V4-Pro-0813-NVFP4 \
  --tp 8 \
  --moe-runner-backend flashinfer_trtllm_routed \
  --speculative-algorithm DSPARK \
  --chunked-prefill-size 8192 \
  --disable-flashinfer-autotune \
  --swa-full-tokens-ratio 0.1 \
  --host 0.0.0.0 \
  --port 30000
```

**p6-b300.48xlarge（8×B300） · 策略 `low-latency` · cookbook 状态：in-progress** · [cookbook 原始配置](https://docs.sglang.io/cookbook/autoregressive/DeepSeek/DeepSeek-V4#hw=b300&variant=pro-official&quant=nvfp4&strategy=low-latency&nodes=single&pdMode=prefill)

```bash
sglang serve \
  --trust-remote-code \
  --model-path nvidia/DeepSeek-V4-Pro-0813-NVFP4 \
  --tp 8 \
  --moe-runner-backend flashinfer_trtllm_routed \
  --speculative-algorithm DSPARK \
  --chunked-prefill-size 8192 \
  --disable-flashinfer-autotune \
  --swa-full-tokens-ratio 0.1 \
  --mem-fraction-static 0.90 \
  --host 0.0.0.0 \
  --port 30000
```

### Qwen3.8-2.4T-NVFP4（`RadixArk/Qwen3.8-2.4T-A95B-NVFP4`）

来源：[SGLang cookbook](https://docs.sglang.io/cookbook/autoregressive/Qwen/Qwen3.8)。下面每种机型只列一条（优先 cookbook 标为 verified 的），其余策略见 cookbook 页面。

**p6-b300.48xlarge（8×B300） · 策略 `balanced` · cookbook 状态：verified** · [cookbook 原始配置](https://docs.sglang.io/cookbook/autoregressive/Qwen/Qwen3.8#hw=b300&variant=default&quant=nvfp4&strategy=balanced&nodes=single)

```bash
sglang serve \
  --trust-remote-code \
  --model-path RadixArk/Qwen3.8-2.4T-A95B-NVFP4 \
  --tp-size 8 \
  --moe-runner-backend flashinfer_trtllm \
  --flashinfer-allreduce-fusion-backend cutedsl \
  --mamba-radix-cache-strategy extra_buffer \
  --mamba-ssm-dtype bfloat16 \
  --speculative-algorithm NEXTN \
  --speculative-num-steps 3 \
  --speculative-eagle-topk 1 \
  --speculative-num-draft-tokens 4 \
  --enable-linear-replayssm-spec \
  --mem-fraction-static 0.90 \
  --chunked-prefill-size 8192 \
  --max-prefill-tokens 8192 \
  --reasoning-parser qwen3 \
  --tool-call-parser qwen3_coder \
  --host 0.0.0.0 \
  --port 30000
```

### Qwen3.8-27B（`Qwen/Qwen3.8-27B`）

来源：[SGLang cookbook](https://docs.sglang.io/cookbook/autoregressive/Qwen/Qwen3.8-27B)。下面每种机型只列一条（优先 cookbook 标为 verified 的），其余策略见 cookbook 页面。

**p5en.48xlarge / p5e.48xlarge（8×H200 141GB） · 策略 `high-throughput` · cookbook 状态：verified** · [cookbook 原始配置](https://docs.sglang.io/cookbook/autoregressive/Qwen/Qwen3.8-27B#hw=h200&variant=default&quant=bf16&nodes=single&spec=none&tier=high-throughput&ssmDtype=float32)

```bash
sglang serve \
  --trust-remote-code \
  --model-path Qwen/Qwen3.8-27B \
  --kv-cache-dtype fp8_e4m3 \
  --mem-fraction-static 0.85 \
  --attention-backend flashinfer \
  --chunked-prefill-size 32768 \
  --max-prefill-tokens 32768 \
  --reasoning-parser qwen3 \
  --tool-call-parser qwen3_coder \
  --host 0.0.0.0 \
  --port 30000 \
  --mamba-radix-cache-strategy extra_buffer_lazy \
  --mamba-ssm-dtype float32
```

### GLM-5.3（`zai-org/GLM-5.3`）

来源：[SGLang cookbook](https://docs.sglang.io/cookbook/autoregressive/GLM/GLM-5.3)。下面每种机型只列一条（优先 cookbook 标为 verified 的），其余策略见 cookbook 页面。

**p5en.48xlarge / p5e.48xlarge（8×H200 141GB） · 策略 `high-throughput` · cookbook 状态：verified** · [cookbook 原始配置](https://docs.sglang.io/cookbook/autoregressive/GLM/GLM-5.3#hw=h200&variant=default&quant=fp8&strategy=high-throughput&nodes=single&pdMode=unified&parsers=auto)

```bash
sglang serve \
  --model-path zai-org/GLM-5.3 \
  --tp 8 \
  --attn-dp-size 8 \
  --moe-a2a-backend deepep \
  --speculative-algorithm EAGLE \
  --speculative-num-steps 1 \
  --speculative-eagle-topk 1 \
  --speculative-num-draft-tokens 2 \
  --mem-fraction-static 0.85 \
  --chunked-prefill-size 32768 \
  --max-running-requests 256 \
  --host 0.0.0.0 \
  --port 30000 \
  --reasoning-parser auto \
  --tool-call-parser auto
```

**p6-b200.48xlarge（8×B200） · 策略 `high-throughput` · cookbook 状态：verified** · [cookbook 原始配置](https://docs.sglang.io/cookbook/autoregressive/GLM/GLM-5.3#hw=b200&variant=default&quant=fp8&strategy=high-throughput&nodes=single&pdMode=unified&parsers=auto)

```bash
sglang serve \
  --model-path zai-org/GLM-5.3 \
  --tp 8 \
  --attn-dp-size 8 \
  --moe-a2a-backend deepep \
  --speculative-algorithm EAGLE \
  --speculative-num-steps 1 \
  --speculative-eagle-topk 1 \
  --speculative-num-draft-tokens 2 \
  --mem-fraction-static 0.85 \
  --chunked-prefill-size 32768 \
  --max-running-requests 256 \
  --host 0.0.0.0 \
  --port 30000 \
  --reasoning-parser auto \
  --tool-call-parser auto
```

**p6-b300.48xlarge（8×B300） · 策略 `high-throughput` · cookbook 状态：verified** · [cookbook 原始配置](https://docs.sglang.io/cookbook/autoregressive/GLM/GLM-5.3#hw=b300&variant=default&quant=fp8&strategy=high-throughput&nodes=single&pdMode=unified&parsers=auto)

```bash
sglang serve \
  --model-path zai-org/GLM-5.3 \
  --tp 8 \
  --attn-dp-size 8 \
  --moe-a2a-backend deepep \
  --speculative-algorithm EAGLE \
  --speculative-num-steps 1 \
  --speculative-eagle-topk 1 \
  --speculative-num-draft-tokens 2 \
  --mem-fraction-static 0.85 \
  --chunked-prefill-size 32768 \
  --max-running-requests 256 \
  --host 0.0.0.0 \
  --port 30000 \
  --reasoning-parser auto \
  --tool-call-parser auto
```

### GLM-5.3-Flash（`zai-org/GLM-5.3-Flash`）

来源：[SGLang cookbook](https://docs.sglang.io/cookbook/autoregressive/GLM/GLM-5.3-Flash)。下面每种机型只列一条（优先 cookbook 标为 verified 的），其余策略见 cookbook 页面。

**p5.48xlarge（8×H100 80GB） · 策略 `high-throughput` · cookbook 状态：verified** · [cookbook 原始配置](https://docs.sglang.io/cookbook/autoregressive/GLM/GLM-5.3-Flash#hw=h100&strategy=high-throughput&quant=fp8&pdMode=unified&kvDsaPair=bf16-tilelang&bcg=off&mmTransport=auto&hicache=off&parsers=auto)

```bash
sglang serve \
  --model-path zai-org/GLM-5.3-Flash \
  --tp-size 8 \
  --ep-size 8 \
  --mem-fraction-static 0.75 \
  --dsa-prefill-backend tilelang \
  --dsa-decode-backend tilelang \
  --kv-cache-dtype bfloat16 \
  --moe-runner-backend deep_gemm \
  --mamba-full-memory-ratio 0.9 \
  --host 0.0.0.0 \
  --port 30000 \
  --reasoning-parser auto \
  --tool-call-parser auto
```

**p5en.48xlarge / p5e.48xlarge（8×H200 141GB） · 策略 `high-throughput` · cookbook 状态：verified** · [cookbook 原始配置](https://docs.sglang.io/cookbook/autoregressive/GLM/GLM-5.3-Flash#hw=h200&strategy=high-throughput&quant=fp8&pdMode=unified&kvDsaPair=bf16-tilelang&bcg=off&mmTransport=auto&hicache=off&parsers=auto)

```bash
sglang serve \
  --model-path zai-org/GLM-5.3-Flash \
  --tp-size 8 \
  --ep-size 8 \
  --dsa-prefill-backend tilelang \
  --dsa-decode-backend tilelang \
  --kv-cache-dtype bfloat16 \
  --moe-runner-backend deep_gemm \
  --mamba-full-memory-ratio 0.9 \
  --host 0.0.0.0 \
  --port 30000 \
  --reasoning-parser auto \
  --tool-call-parser auto
```

**p6-b200.48xlarge（8×B200） · 策略 `high-throughput` · cookbook 状态：in-progress** · [cookbook 原始配置](https://docs.sglang.io/cookbook/autoregressive/GLM/GLM-5.3-Flash#hw=b200&strategy=high-throughput&quant=fp8&pdMode=unified&kvDsaPair=fp8-trtllm&bcg=off&mmTransport=auto&hicache=off&parsers=auto)

```bash
# Measured on GB300: faster than BF16 + TileLang with about 1.8x the KV token capacity.
sglang serve \
  --model-path zai-org/GLM-5.3-Flash \
  --tp-size 8 \
  --dsa-prefill-backend trtllm \
  --dsa-decode-backend trtllm \
  --kv-cache-dtype fp8_e4m3 \
  --moe-runner-backend flashinfer_trtllm \
  --host 0.0.0.0 \
  --port 30000 \
  --reasoning-parser auto \
  --tool-call-parser auto
```

**p6-b300.48xlarge（8×B300） · 策略 `high-throughput` · cookbook 状态：in-progress** · [cookbook 原始配置](https://docs.sglang.io/cookbook/autoregressive/GLM/GLM-5.3-Flash#hw=b300&strategy=high-throughput&quant=fp8&pdMode=unified&kvDsaPair=fp8-trtllm&bcg=off&mmTransport=auto&hicache=off&parsers=auto)

```bash
# Measured on GB300: faster than BF16 + TileLang with about 1.8x the KV token capacity.
sglang serve \
  --model-path zai-org/GLM-5.3-Flash \
  --tp-size 8 \
  --dsa-prefill-backend trtllm \
  --dsa-decode-backend trtllm \
  --kv-cache-dtype fp8_e4m3 \
  --moe-runner-backend flashinfer_trtllm \
  --host 0.0.0.0 \
  --port 30000 \
  --reasoning-parser auto \
  --tool-call-parser auto
```

### Kimi-K3.1-Pro（`moonshotai/Kimi-K3.1-Pro`）

来源：[SGLang cookbook](https://docs.sglang.io/cookbook/autoregressive/Moonshotai/Kimi-K3.1-Pro)。下面每种机型只列一条（优先 cookbook 标为 verified 的），其余策略见 cookbook 页面。

**p6-b300.48xlarge（8×B300） · 策略 `low-latency` · cookbook 状态：in-progress** · [cookbook 原始配置](https://docs.sglang.io/cookbook/autoregressive/Moonshotai/Kimi-K3.1-Pro#hw=b300&pdMode=unified&strategy=low-latency&spec=dflash&hicache=off)

```bash
export SGLANG_ENABLE_DFLASH_DRAFT_KV_RING=1
SGLANG_ENABLE_DFLASH_DRAFT_KV_RING=1 \
sglang serve \
  --trust-remote-code \
  --model-path moonshotai/Kimi-K3.1-Pro \
  --tp-size 8 \
  --mem-fraction-static 0.85 \
  --max-running-requests 64 \
  --weight-loader-prefetch-checkpoints \
  --model-loader-extra-config '{"enable_multithread_load": true}' \
  --reasoning-parser kimi_k3 \
  --tool-call-parser kimi_k3 \
  --host 0.0.0.0 \
  --port 30000 \
  --speculative-algorithm DFLASH \
  --speculative-draft-model-path RadixArk/Kimi-K3.1-Dflash2-Preview \
  --speculative-dflash-block-size 8 \
  --speculative-draft-kv-cache-dtype fp8_e4m3 \
  --speculative-draft-attention-backend cutedsl_mla \
  --enable-linear-replayssm-spec
```

### MiniMax-M3.1-Flash（`MiniMaxAI/MiniMax-M3.1-Flash`）

来源：[SGLang cookbook](https://docs.sglang.io/cookbook/autoregressive/MiniMax/MiniMax-M3.1)。下面每种机型只列一条（优先 cookbook 标为 verified 的），其余策略见 cookbook 页面。

**p5en.48xlarge / p5e.48xlarge（8×H200 141GB） · 策略 `balanced` · cookbook 状态：verified** · [cookbook 原始配置](https://docs.sglang.io/cookbook/autoregressive/MiniMax/MiniMax-M3.1#hw=h200&variant=flash&quant=nvfp4&strategy=balanced&nodes=single&spec=dspark)

```bash
sglang serve \
  --trust-remote-code \
  --model-path MiniMaxAI/MiniMax-M3.1-Flash \
  --reasoning-parser minimax-m3 \
  --tool-call-parser minimax-m3 \
  --tp 8 \
  --context-length 140000 \
  --cuda-graph-backend-prefill breakable \
  --mem-fraction-static 0.85 \
  --cuda-graph-max-bs-decode 64 \
  --tokenizer-worker-num 8 \
  --host 0.0.0.0 \
  --port 30000
```

**p6-b200.48xlarge（8×B200） · 策略 `balanced` · cookbook 状态：in-progress** · [cookbook 原始配置](https://docs.sglang.io/cookbook/autoregressive/MiniMax/MiniMax-M3.1#hw=b200&variant=flash&quant=nvfp4&strategy=balanced&nodes=single&spec=dspark)

```bash
export FMHA_SM100_ALLOW_JIT=1
FMHA_SM100_ALLOW_JIT=1 \
sglang serve \
  --trust-remote-code \
  --model-path MiniMaxAI/MiniMax-M3.1-Flash \
  --reasoning-parser minimax-m3 \
  --tool-call-parser minimax-m3 \
  --tp 4 \
  --moe-runner-backend flashinfer_trtllm_routed \
  --speculative-algorithm DSPARK \
  --speculative-use-block-verification \
  --cuda-graph-backend-prefill breakable \
  --chunked-prefill-size 32768 \
  --max-running-requests 128 \
  --cuda-graph-max-bs-decode 128 \
  --mem-fraction-static 0.8 \
  --tokenizer-worker-num 8 \
  --host 0.0.0.0 \
  --port 30000
```

**p6-b300.48xlarge（8×B300） · 策略 `balanced` · cookbook 状态：verified** · [cookbook 原始配置](https://docs.sglang.io/cookbook/autoregressive/MiniMax/MiniMax-M3.1#hw=b300&variant=flash&quant=nvfp4&strategy=balanced&nodes=single&spec=dspark)

```bash
export FMHA_SM100_ALLOW_JIT=1
FMHA_SM100_ALLOW_JIT=1 \
sglang serve \
  --trust-remote-code \
  --model-path MiniMaxAI/MiniMax-M3.1-Flash \
  --reasoning-parser minimax-m3 \
  --tool-call-parser minimax-m3 \
  --tp 4 \
  --moe-runner-backend flashinfer_trtllm_routed \
  --speculative-algorithm DSPARK \
  --speculative-use-block-verification \
  --cuda-graph-backend-prefill breakable \
  --chunked-prefill-size 32768 \
  --max-running-requests 128 \
  --cuda-graph-max-bs-decode 128 \
  --mem-fraction-static 0.8 \
  --tokenizer-worker-num 8 \
  --host 0.0.0.0 \
  --port 30000
```

### Mistral-Large-4（`mistralai/Mistral-Large-4-1T-A52B`）

来源：[SGLang cookbook](https://docs.sglang.io/cookbook/autoregressive/Mistral/Mistral-Large-4)。下面每种机型只列一条（优先 cookbook 标为 verified 的），其余策略见 cookbook 页面。

**p6-b200.48xlarge（8×B200） · 策略 `high-throughput` · cookbook 状态：unverified** · [cookbook 原始配置](https://docs.sglang.io/cookbook/autoregressive/Mistral/Mistral-Large-4#hw=b200&variant=default&quant=fp8&strategy=high-throughput&nodes=single)

```bash
sglang serve \
  --model-path mistralai/Mistral-Large-4-1T-A52B \
  --tp-size 8 \
  --mem-fraction-static 0.85 \
  --reasoning-parser auto \
  --tool-call-parser auto \
  --host 0.0.0.0 \
  --port 30000
```

**p6-b300.48xlarge（8×B300） · 策略 `high-throughput` · cookbook 状态：verified** · [cookbook 原始配置](https://docs.sglang.io/cookbook/autoregressive/Mistral/Mistral-Large-4#hw=b300&variant=default&quant=fp8&strategy=high-throughput&nodes=single)

```bash
sglang serve \
  --model-path mistralai/Mistral-Large-4-1T-A52B \
  --tp-size 8 \
  --mem-fraction-static 0.85 \
  --reasoning-parser auto \
  --tool-call-parser auto \
  --host 0.0.0.0 \
  --port 30000
```
### gpt-oss-120b（`openai/gpt-oss-120b`）

来源：[SGLang cookbook · GPT-OSS](https://docs.sglang.io/cookbook/autoregressive/OpenAI/GPT-OSS)。cookbook 的速度基准用 8×B200、TP8、SGLang 0.5.6；命令本身不区分硬件，可在 `p5.48xlarge` 或 `p6-b200.48xlarge` 上使用。

```bash
python -m sglang.launch_server \
  --model openai/gpt-oss-120b \
  --reasoning-parser gpt-oss \
  --tool-call-parser gpt-oss \
  --tp 8
```

注意这条命令没有指定 `--port`，默认端口是 30000。

### Qwen3-Omni-30B-A3B-Instruct

矩阵中是 🟡：SGLang 只支持 Thinker（文本输出），没有 cookbook 页面，所以这里不给命令。要文本+语音输出请用 [vLLM-Omni](vllm-omni.md)。
