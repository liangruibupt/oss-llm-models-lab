# 🛠 vLLM-Omni 实践：Qwen3-Omni-30B-A3B-Instruct

> **checked 2026-11-27**，命令来自 [vLLM-Omni Qwen3-Omni recipe](https://github.com/vllm-project/vllm-omni/blob/main/recipes/Qwen/Qwen3-Omni.md) 与 [在线服务示例](https://github.com/vllm-project/vllm-omni/blob/main/docs/user_guide/examples/online_serving/qwen3_omni.md)（vllm-omni@`c183bab`，v0.34.0），**未在本仓库实测**。矩阵中 vLLM-Omni 只有这一个 ✅（其余为纯文本 LLM，记 ➖）。

## 部署形态

Qwen3-Omni 在 vLLM-Omni 里拆成 3 个 stage：Thinker（多模态理解，输出文本）、Talker（生成语音 codec）、Code2Wav（还原波形）。默认部署配置 [`qwen3_omni_moe.yaml`](https://github.com/vllm-project/vllm-omni/blob/main/vllm_omni/deploy/qwen3_omni_moe.yaml) 在 CUDA 上用 **2 张卡**：stage 0 在 GPU 0（`gpu_memory_utilization: 0.9`），stage 1 和 2 共用 GPU 1。

| AWS 机型 | 是否官方配置 | 说明 |
|---|---|---|
| `p5.48xlarge`（8×H100 80GB） | 默认配置可直接用（只占 2 张卡） | 最稳妥，但 8 卡只用 2 张 |
| `g6e.12xlarge`（4×L40S 48GB） | **非官方**，需自写 overlay 把 Thinker 改为 TP2 | Thinker BF16 权重约 60 GB，放不进单张 48GB；可参照 yaml 里 NPU 平台的 TP2 写法，待实测 |

## 安装与启动

按 [安装文档](https://vllm-omni.readthedocs.io/en/latest/getting_started/installation/) 安装 vLLM + vLLM-Omni（或使用 [Docker 镜像](https://hub.docker.com/r/vllm/vllm-omni/tags)），然后：

```bash
vllm serve Qwen/Qwen3-Omni-30B-A3B-Instruct --omni --port 8091
```

`--omni` 必须加。自定义拓扑时传 overlay：

```bash
vllm serve Qwen/Qwen3-Omni-30B-A3B-Instruct --omni --port 8091 \
  --deploy-config /path/to/your_qwen3_omni_overrides.yaml
```

## 发请求

只要文本输出（跳过语音 stage，速度更快）：

```bash
curl http://localhost:8091/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen/Qwen3-Omni-30B-A3B-Instruct",
    "messages": [{"role": "user", "content": "Describe vLLM in brief."}],
    "modalities": ["text"]
  }'
```

`modalities` 可取 `["text"]`、`["audio"]`、`["text", "audio"]`，不传时默认文本+语音。

## 压测

本仓库的 harness 只统计文本 token，适合测 Thinker 的文本路径：

```bash
python bench/llm_bench.py --base-url http://127.0.0.1:8091/v1 \
  --model Qwen/Qwen3-Omni-30B-A3B-Instruct \
  --extra-body '{"modalities": ["text"]}' \
  --input-len 1024 --output-len 256 --concurrency 1,8,32,64 \
  --label "vLLM-Omni 0.34 / p5.48xlarge / BF16 / text-only" --out results/qwen3omni_vllmomni_p5
```

语音输出的延迟（首包音频时间、实时率）需要专门的音频指标，当前 harness 不覆盖。
