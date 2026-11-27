# 🛠 vLLM 实践：在 AWS 上启动矩阵中的 ✅ 组合

> **checked 2026-11-27**，命令取自 [vLLM Recipes](https://recipes.vllm.ai/) 的 JSON API（`https://recipes.vllm.ai/<hf_id>/hw/<hw>.json`，recipes@`4744321`），只做了 AWS 机型映射，**未在本仓库实测**。「recipe 状态」是 recipe 文件里该硬件的标记。实测计划见 [`../BENCH_PLAN.md`](../BENCH_PLAN.md)。

## AWS 机型映射

| recipe 硬件 | AWS 实例 |
|---|---|
| `h100` | `p5.48xlarge`（8×H100 80GB） |
| `h200` | `p5en.48xlarge` / `p5e.48xlarge`（8×H200 141GB） |
| `b200` | `p6-b200.48xlarge`（8×B200） |
| `b300` | `p6-b300.48xlarge`（8×B300） |

只列出 recipe 在这四种硬件上给了命令的组合。recipe 的其他硬件（GB200/GB300、MI3xx、昇腾、TPU 等）请在 recipe 页面切换查看。

## 通用步骤

1. AWS Deep Learning AMI + Docker + NVIDIA Container Toolkit，权重放实例 NVMe 或大容量 EBS。
2. 用 recipe 给出的镜像启动（recipe 的 `docker_command` 形式）：

```bash
docker run --gpus all --privileged --ipc=host -p 8000:8000 \
  -v ~/.cache/huggingface:/root/.cache/huggingface \
  -e HF_TOKEN \
  vllm/vllm-openai:latest <下面 vllm serve 之后的参数>
```

不同模型的镜像标签不同（`latest`、`nightly`、`qwen38`、`minimax-m31-flash`），以每节标注为准；下面的 `export` 行在 `docker run` 里改成 `-e KEY=VALUE`。

3. 发一个请求：

```bash
MODEL=openai/gpt-oss-120b   # 与 vllm serve 的模型参数相同
curl -s http://127.0.0.1:8000/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{"model": "'"$MODEL"'", "messages": [{"role": "user", "content": "用一句话介绍你自己"}], "max_tokens": 128}'
```

4. 压测：`python bench/llm_bench.py --base-url http://127.0.0.1:8000/v1 --model "$MODEL" ...`（见 [`../../bench/README.md`](../../bench/README.md)）。

5. 用完立刻停止或终止实例。

## 各模型启动命令

### `deepseek-ai/DeepSeek-V4.1-Flash`

来源：[vLLM Recipes](https://recipes.vllm.ai/deepseek-ai/DeepSeek-V4.1-Flash)（JSON API `https://recipes.vllm.ai/deepseek-ai/DeepSeek-V4.1-Flash/hw/<hw>.json`，checked 2026-11-27）。

**p5.48xlarge（8×H100 80GB） · single_node_tp · 1 节点 · recipe 状态：verified · 镜像 `vllm/vllm-openai:latest`**

```bash
export VLLM_ENGINE_READY_TIMEOUT_S=3600 VLLM_USE_V2_MODEL_RUNNER=1 PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True VLLM_USE_RUST_FRONTEND=1
vllm serve deepseek-ai/DeepSeek-V4.1-Flash-1017 \
  --tokenizer-mode deepseek_v41 \
  --engram-config '{"cpu_offload":true}' \
  --max-num-batched-tokens 4096 \
  --tensor-parallel-size 8 \
  --tool-call-parser deepseek_v41 \
  --enable-auto-tool-choice \
  --reasoning-parser deepseek_v41 \
  --mm-encoder-tp-mode data
```

**p5en.48xlarge / p5e.48xlarge（8×H200 141GB） · single_node_tp · 1 节点 · recipe 状态：verified · 镜像 `vllm/vllm-openai:latest`**

```bash
export VLLM_ENGINE_READY_TIMEOUT_S=3600 VLLM_USE_RUST_FRONTEND=1
vllm serve deepseek-ai/DeepSeek-V4.1-Flash-1017 \
  --tokenizer-mode deepseek_v41 \
  --tensor-parallel-size 4 \
  --engram-config '{"cpu_offload":true}' \
  --tool-call-parser deepseek_v41 \
  --enable-auto-tool-choice \
  --reasoning-parser deepseek_v41 \
  --mm-encoder-tp-mode data
```

**p6-b200.48xlarge（8×B200） · single_node_tp · 1 节点 · recipe 状态：verified · 镜像 `vllm/vllm-openai:latest`**

```bash
export VLLM_ENGINE_READY_TIMEOUT_S=3600 VLLM_USE_RUST_FRONTEND=1
vllm serve deepseek-ai/DeepSeek-V4.1-Flash-1017 \
  --tokenizer-mode deepseek_v41 \
  --tensor-parallel-size 2 \
  --attention-config '{"backend":"FLASHINFER_MLA_SPARSE_DSV41","indexer_kv_dtype":"mxfp4","indexer_sparse_logits":true}' \
  --kv-cache-dtype fp8 \
  --max-num-seqs 128 \
  --engram-config '{"cpu_offload":true}' \
  --tool-call-parser deepseek_v41 \
  --enable-auto-tool-choice \
  --reasoning-parser deepseek_v41 \
  --mm-encoder-tp-mode data
```

**p6-b300.48xlarge（8×B300） · single_node_tp · 1 节点 · recipe 状态：verified · 镜像 `vllm/vllm-openai:latest`**

```bash
export VLLM_ENGINE_READY_TIMEOUT_S=3600 VLLM_USE_RUST_FRONTEND=1
vllm serve deepseek-ai/DeepSeek-V4.1-Flash-1017 \
  --tokenizer-mode deepseek_v41 \
  --tensor-parallel-size 2 \
  --attention-config '{"backend":"FLASHINFER_MLA_SPARSE_DSV41","indexer_kv_dtype":"mxfp4","indexer_sparse_logits":true}' \
  --kv-cache-dtype fp8 \
  --engram-config '{"cpu_offload":true}' \
  --compilation-config '{"mode":"VLLM_COMPILE","cudagraph_mode":"FULL_AND_PIECEWISE","cudagraph_capture_sizes":[6,12,18,24,30,36,48,60,72,96,120,144,192,240,288,384,480,576,768,1020,1536,2046,3072,4092,6144,8190]}' \
  --max-cudagraph-capture-size 8190 \
  --max-num-batched-tokens 8192 \
  --max-num-seqs 256 \
  --tool-call-parser deepseek_v41 \
  --enable-auto-tool-choice \
  --reasoning-parser deepseek_v41 \
  --mm-encoder-tp-mode data
```

### `deepseek-ai/DeepSeek-V4-Pro`

来源：[vLLM Recipes](https://recipes.vllm.ai/deepseek-ai/DeepSeek-V4-Pro)（JSON API `https://recipes.vllm.ai/deepseek-ai/DeepSeek-V4-Pro/hw/<hw>.json`，checked 2026-11-27）。

**p5en.48xlarge / p5e.48xlarge（8×H200 141GB） · single_node_tep · 1 节点 · recipe 状态：verified · 镜像 `vllm/vllm-openai:latest`**

```bash
export VLLM_USE_RUST_FRONTEND=1
vllm serve deepseek-ai/DeepSeek-V4-Pro-0813 \
  --trust-remote-code \
  --kv-cache-dtype fp8 \
  --block-size 256 \
  --enable-expert-parallel \
  --tensor-parallel-size 8 \
  --max-model-len 800000 \
  --max-num-seqs 512 \
  --disable-flashinfer-autotune \
  --compilation-config '{"mode": 0, "cudagraph_mode": "FULL_DECODE_ONLY"}' \
  --tokenizer-mode deepseek_v4 \
  --tool-call-parser deepseek_v4 \
  --enable-auto-tool-choice \
  --reasoning-parser deepseek_v4 \
  --speculative-config '{"method":"dspark","num_speculative_tokens":7,"draft_sample_method":"probabilistic"}'
```

**p6-b200.48xlarge（8×B200） · single_node_tep · 1 节点 · recipe 状态：verified · 镜像 `vllm/vllm-openai:latest`**

```bash
export VLLM_USE_RUST_FRONTEND=1
vllm serve deepseek-ai/DeepSeek-V4-Pro-0813 \
  --trust-remote-code \
  --kv-cache-dtype fp8 \
  --block-size 256 \
  --enable-expert-parallel \
  --tensor-parallel-size 8 \
  --compilation-config '{"cudagraph_mode":"FULL_AND_PIECEWISE", "custom_ops":["all"]}' \
  --attention_config.indexer_kv_dtype=mxfp4 \
  --moe-backend deep_gemm_mega_moe \
  --tokenizer-mode deepseek_v4 \
  --tool-call-parser deepseek_v4 \
  --enable-auto-tool-choice \
  --reasoning-parser deepseek_v4 \
  --speculative-config '{"method":"dspark","num_speculative_tokens":7,"draft_sample_method":"probabilistic"}'
```

**p6-b300.48xlarge（8×B300） · single_node_tep · 1 节点 · recipe 状态：verified · 镜像 `vllm/vllm-openai:latest`**

```bash
export VLLM_USE_RUST_FRONTEND=1
vllm serve deepseek-ai/DeepSeek-V4-Pro-0813 \
  --trust-remote-code \
  --kv-cache-dtype fp8 \
  --block-size 256 \
  --enable-expert-parallel \
  --tensor-parallel-size 8 \
  --compilation-config '{"cudagraph_mode":"FULL_AND_PIECEWISE", "custom_ops":["all"]}' \
  --attention_config.indexer_kv_dtype=mxfp4 \
  --moe-backend deep_gemm_mega_moe \
  --tokenizer-mode deepseek_v4 \
  --tool-call-parser deepseek_v4 \
  --enable-auto-tool-choice \
  --reasoning-parser deepseek_v4 \
  --speculative-config '{"method":"dspark","num_speculative_tokens":7,"draft_sample_method":"probabilistic"}'
```

### `Qwen/Qwen3.8-2.4T-A95B`

来源：[vLLM Recipes](https://recipes.vllm.ai/Qwen/Qwen3.8-2.4T-A95B)（JSON API `https://recipes.vllm.ai/Qwen/Qwen3.8-2.4T-A95B/hw/<hw>.json`，checked 2026-11-27）。

**p6-b300.48xlarge（8×B300） · multi_node_tp · 2 节点 · recipe 状态：verified · 镜像 `vllm/vllm-openai:qwen38`**

```bash
export VLLM_ENGINE_READY_TIMEOUT_S=3600 GLOO_SOCKET_IFNAME=$IFACE_NAME NCCL_SOCKET_IFNAME=$IFACE_NAME VLLM_USE_RUST_FRONTEND=1
# 节点 0（head）
vllm serve Qwen/Qwen3.8-2.4T-A95B \
  --tensor-parallel-size 16 \
  --nnodes 2 \
  --node-rank 0 \
  --master-addr $HEAD_IP \
  --enable-auto-tool-choice \
  --tool-call-parser qwen3_coder \
  --reasoning-parser qwen3

# 节点 1（worker）
vllm serve Qwen/Qwen3.8-2.4T-A95B \
  --tensor-parallel-size 16 \
  --nnodes 2 \
  --node-rank 1 \
  --master-addr $HEAD_IP \
  --headless \
  --enable-auto-tool-choice \
  --tool-call-parser qwen3_coder \
  --reasoning-parser qwen3
```

### `Qwen/Qwen3.8-27B`

来源：[vLLM Recipes](https://recipes.vllm.ai/Qwen/Qwen3.8-27B)（JSON API `https://recipes.vllm.ai/Qwen/Qwen3.8-27B/hw/<hw>.json`，checked 2026-11-27）。

**p6-b200.48xlarge（8×B200） · single_node_tp · 1 节点 · recipe 状态：verified · 镜像 `vllm/vllm-openai:qwen38`**

```bash
export VLLM_USE_RUST_FRONTEND=1
vllm serve Qwen/Qwen3.8-27B \
  --tensor-parallel-size 1 \
  --enable-auto-tool-choice \
  --tool-call-parser qwen3_coder \
  --reasoning-parser qwen3 \
  --mm-encoder-tp-mode data
```

### `zai-org/GLM-5.3`

来源：[vLLM Recipes](https://recipes.vllm.ai/zai-org/GLM-5.3)（JSON API `https://recipes.vllm.ai/zai-org/GLM-5.3/hw/<hw>.json`，checked 2026-11-27）。

**p5en.48xlarge / p5e.48xlarge（8×H200 141GB） · single_node_tp · 1 节点 · recipe 状态：verified · 镜像 `vllm/vllm-openai:latest`**

```bash
export VLLM_USE_RUST_FRONTEND=1
vllm serve zai-org/GLM-5.3 \
  --tokenizer-mode glm5_next \
  --max-model-len 262144 \
  --tensor-parallel-size 8 \
  --kv-cache-dtype fp8 \
  --tool-call-parser glm47 \
  --enable-auto-tool-choice \
  --reasoning-parser glm47
```

**p6-b300.48xlarge（8×B300） · single_node_tp · 1 节点 · recipe 状态：verified · 镜像 `vllm/vllm-openai:latest`**

```bash
export VLLM_USE_RUST_FRONTEND=1
vllm serve zai-org/GLM-5.3 \
  --tokenizer-mode glm5_next \
  --kv-cache-dtype fp8_e4m3 \
  --tensor-parallel-size 8 \
  --tool-call-parser glm47 \
  --enable-auto-tool-choice \
  --reasoning-parser glm47
```

### `zai-org/GLM-5.3-Flash`

来源：[vLLM Recipes](https://recipes.vllm.ai/zai-org/GLM-5.3-Flash)（JSON API `https://recipes.vllm.ai/zai-org/GLM-5.3-Flash/hw/<hw>.json`，checked 2026-11-27）。

**p5.48xlarge（8×H100 80GB） · single_node_tp · 1 节点 · recipe 状态：verified · 镜像 `vllm/vllm-openai:nightly`**

```bash
export VLLM_ENGINE_READY_TIMEOUT_S=3600 VLLM_USE_RUST_FRONTEND=1
vllm serve zai-org/GLM-5.3-Flash \
  --tokenizer-mode glm5_next \
  --tensor-parallel-size 8 \
  --disable-flashinfer-autotune \
  --tool-call-parser glm47 \
  --enable-auto-tool-choice \
  --reasoning-parser glm47
```

**p5en.48xlarge / p5e.48xlarge（8×H200 141GB） · single_node_tp · 1 节点 · recipe 状态：verified · 镜像 `vllm/vllm-openai:nightly`**

```bash
export VLLM_ENGINE_READY_TIMEOUT_S=3600 VLLM_USE_RUST_FRONTEND=1
vllm serve zai-org/GLM-5.3-Flash \
  --tokenizer-mode glm5_next \
  --tensor-parallel-size 8 \
  --disable-flashinfer-autotune \
  --tool-call-parser glm47 \
  --enable-auto-tool-choice \
  --reasoning-parser glm47
```

**p6-b200.48xlarge（8×B200） · single_node_tp · 1 节点 · recipe 状态：verified · 镜像 `vllm/vllm-openai:nightly`**

```bash
export VLLM_ENGINE_READY_TIMEOUT_S=3600 VLLM_USE_RUST_FRONTEND=1
vllm serve zai-org/GLM-5.3-Flash \
  --tokenizer-mode glm5_next \
  --tensor-parallel-size 8 \
  --kv-cache-dtype fp8 \
  --tool-call-parser glm47 \
  --enable-auto-tool-choice \
  --reasoning-parser glm47
```

### `MiniMaxAI/MiniMax-M3.1-Flash`

来源：[vLLM Recipes](https://recipes.vllm.ai/MiniMaxAI/MiniMax-M3.1-Flash)（JSON API `https://recipes.vllm.ai/MiniMaxAI/MiniMax-M3.1-Flash/hw/<hw>.json`，checked 2026-11-27）。

**p6-b300.48xlarge（8×B300） · single_node_tp · 1 节点 · recipe 状态：verified · 镜像 `vllm/vllm-openai:minimax-m31-flash`**

```bash
export VLLM_FLOAT32_MATMUL_PRECISION=high
vllm serve MiniMaxAI/MiniMax-M3.1-Flash \
  --block-size 128 \
  --disable-hybrid-kv-cache-manager \
  --tensor-parallel-size 8 \
  --kv-cache-dtype nvfp4 \
  --attention-config '{"indexer_kv_dtype": "nvfp4", "use_prefill_query_quantization": true}' \
  --compilation-config '{"cudagraph_mode": "FULL_AND_PIECEWISE"}' \
  --tool-call-parser minimax_m3 \
  --enable-auto-tool-choice \
  --reasoning-parser minimax_m3 \
  --speculative-config '{"method":"dspark","num_speculative_tokens":7,"attention_backend":"FLASHINFER_TS","kv_cache_dtype":"fp8","draft_sample_method":"probabilistic","rejection_sample_method":"block"}'
```

### `openai/gpt-oss-120b`

来源：[vLLM Recipes](https://recipes.vllm.ai/openai/gpt-oss-120b)（JSON API `https://recipes.vllm.ai/openai/gpt-oss-120b/hw/<hw>.json`，checked 2026-11-27）。

**p5.48xlarge（8×H100 80GB） · single_node_tp · 1 节点 · recipe 状态：verified · 镜像 `vllm/vllm-openai:latest`**

```bash
vllm serve openai/gpt-oss-120b \
  --tensor-parallel-size 8 \
  --tool-call-parser openai \
  --enable-auto-tool-choice
```

**p5en.48xlarge / p5e.48xlarge（8×H200 141GB） · single_node_tp · 1 节点 · recipe 状态：verified · 镜像 `vllm/vllm-openai:latest`**

```bash
vllm serve openai/gpt-oss-120b \
  --tensor-parallel-size 1 \
  --tool-call-parser openai \
  --enable-auto-tool-choice
```

**p6-b200.48xlarge（8×B200） · single_node_tp · 1 节点 · recipe 状态：verified · 镜像 `vllm/vllm-openai:latest`**

```bash
vllm serve openai/gpt-oss-120b \
  --tensor-parallel-size 1 \
  --quantization-config.moe.activation mxfp8 \
  --tool-call-parser openai \
  --enable-auto-tool-choice
```

### `mistralai/Mistral-Large-4-1T-A52B`

来源：[vLLM Recipes](https://recipes.vllm.ai/mistralai/Mistral-Large-4-1T-A52B)（JSON API `https://recipes.vllm.ai/mistralai/Mistral-Large-4-1T-A52B/hw/<hw>.json`，checked 2026-11-27）。

**p6-b200.48xlarge（8×B200） · single_node_tp · 1 节点 · recipe 状态：verified · 镜像 `vllm/vllm-openai:v0.34.0`**

```bash
export VLLM_ENGINE_READY_TIMEOUT_S=6000
vllm serve mistralai/Mistral-Large-4-1T-A52B-NVFP4 \
  --tokenizer-mode mistral \
  --config-format mistral \
  --load-format mistral \
  --max-model-len 262144 \
  --max-num-batched-tokens 8192 \
  --max-num-seqs 128 \
  --tensor-parallel-size 8 \
  --enable-auto-tool-choice \
  --tool-call-parser mistral \
  --reasoning-parser mistral \
  --speculative-config '{"method":"dspark","num_speculative_tokens":3}'
```

**p6-b300.48xlarge（8×B300） · single_node_tp · 1 节点 · recipe 状态：verified · 镜像 `vllm/vllm-openai:v0.34.0`**

```bash
export VLLM_ENGINE_READY_TIMEOUT_S=6000
vllm serve mistralai/Mistral-Large-4-1T-A52B-NVFP4 \
  --tokenizer-mode mistral \
  --config-format mistral \
  --load-format mistral \
  --max-model-len 262144 \
  --max-num-batched-tokens 8192 \
  --max-num-seqs 128 \
  --tensor-parallel-size 8 \
  --enable-auto-tool-choice \
  --tool-call-parser mistral \
  --reasoning-parser mistral \
  --speculative-config '{"method":"dspark","num_speculative_tokens":3}'
```
### `moonshotai/Kimi-K3.1-Pro`

[recipe](https://recipes.vllm.ai/moonshotai/Kimi-K3.1-Pro) 只给了 GB300、VR200、TPU Ironwood 等硬件的命令，没有 H100/H200/B200/B300 单机配置，因此这里不列命令。在 AWS 上对应的是 `p6e-gb300` UltraServer。

### `mistralai/Mistral-Large-4-1T-A52B` 的 H200

recipe 元数据列出 `h200`，但 `hw/h200.json` 在 2026-11-27 返回 404，请在 [recipe 页面](https://recipes.vllm.ai/mistralai/Mistral-Large-4-1T-A52B) 查看。模型卡片另给出官方镜像 `vllm/vllm-openai:mistral-large-4`。

### Qwen3-Omni-30B-A3B-Instruct

矩阵中是 🟡：vLLM 只注册了 Thinker（`Qwen3OmniMoeThinkerForConditionalGeneration`，文本输出），没有 recipe。要文本+语音输出请用 [vLLM-Omni](vllm-omni.md)。
