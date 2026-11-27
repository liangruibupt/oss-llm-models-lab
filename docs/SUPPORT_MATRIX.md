# 📊 支持矩阵：开源 LLM × 推理框架

> **checked 2026-11-27**。所有 ✅/🟡 都附来源链接；源码核对的提交：sglang@`f8fd250`、vllm@`da11057`、vllm-omni@`c183bab`、vllm-project/recipes@`4744321`、trnrt v0.2.0、DeepInfer@`a679bb8`。
> 框架会快速迭代，使用前请以链接里的最新文档为准。

## 图例

| 符号 | 含义 |
|---|---|
| ✅ | 官方支持：框架官方文档 / recipe / cookbook / 模型注册表里有该模型（链接指向该文档） |
| 🟡 | 部分支持：实验性、社区维护、只支持部分组件，或只支持同系列旧型号（单元格内说明） |
| ❌ | 不支持（框架的支持列表里没有，且没有官方 recipe） |
| ➖ | 不适用（框架定位不覆盖这类模型） |

## 模型清单（均已在 Hugging Face 核实存在）

| # | 模型（HF repo） | 发布 | 总参 / 激活 | 上下文 | 许可证 | 备注 |
|---|---|---|---|---|---|---|
| 1 | [deepseek-ai/DeepSeek-V4.1-Flash-1017](https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash-1017) | 2026-10-17 | 552B 主干（另有 196B Engram 记忆表）/ prefill 8B、decode 16B | 1M | MIT | V4.1-Flash 的权重小更新；图文输入 |
| 2 | [deepseek-ai/DeepSeek-V4-Pro-0813](https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro-0813) | 2026-08-13 | 1.6T / 49B（见 [V4-Pro 卡片](https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro)） | 1M | MIT | V4-Pro 正式版 |
| 3 | [Qwen/Qwen3.8-2.4T-A95B](https://huggingface.co/Qwen/Qwen3.8-2.4T-A95B) | 2026-08-08 | 2.4T / 95B | 262K 原生，可扩到 1.01M | Qwen3.8-Max License | Qwen 最大开源权重模型 |
| 4 | [Qwen/Qwen3.8-27B](https://huggingface.co/Qwen/Qwen3.8-27B) | 2026-08-05 | 27B dense | 262K 原生，可扩到 1M | Apache 2.0 | 单卡可跑，适合 g6e |
| 5 | [zai-org/GLM-5.3](https://huggingface.co/zai-org/GLM-5.3) | 2026-08-25 | 约 753B（HF safetensors 计数，卡片未写激活参数；与 GLM-5.2 同 base） | 1M | GLM-5.3 License | — |
| 6 | [zai-org/GLM-5.3-Flash](https://huggingface.co/zai-org/GLM-5.3-Flash) | 2026-08-25 | 320B / 18B | 1M | MIT | TrnRT 首个（也是目前唯一）支持的模型 |
| 7 | [moonshotai/Kimi-K3.1-Pro](https://huggingface.co/moonshotai/Kimi-K3.1-Pro) | 2026-11-02 | 2.8T / 104B | 1M | Kimi K3.1-Pro License | MXFP4 权重 / MXFP8 激活（QAT） |
| 8 | [MiniMaxAI/MiniMax-M3.1-Flash](https://huggingface.co/MiniMaxAI/MiniMax-M3.1-Flash) | 2026-10-17 | 约 428B / 23B | 1M | MiniMax Community License | 图文视频输入 |
| 9 | [openai/gpt-oss-120b](https://huggingface.co/openai/gpt-oss-120b) | 2025-08-04 | 117B / 5.1B | 131K | Apache 2.0 | MXFP4 MoE，单张 80GB 卡可放下 |
| 10 | [mistralai/Mistral-Large-4-1T-A52B](https://huggingface.co/mistralai/Mistral-Large-4-1T-A52B) | 2026-09-30 | 约 1T / 52B（含 embedding 与输出层；不含时 49B） | 1M | Mistral Ecosystem Open-Weight License | 另有 [NVFP4 版](https://huggingface.co/mistralai/Mistral-Large-4-1T-A52B-NVFP4) |
| 11 | [Qwen/Qwen3-Omni-30B-A3B-Instruct](https://huggingface.co/Qwen/Qwen3-Omni-30B-A3B-Instruct) | 2025-09-20 | 30B / 3B（Thinker MoE） | 64K（Thinker `max_position_embeddings`） | Apache 2.0 | any-to-any：文本/图像/音频/视频输入，文本+语音输出 |

参数与上下文均取自各模型卡片或 `config.json`。Llama：meta-llama 在 HF 上最新的仍是 2025-04 的 Llama 4 系列，2026 年没有新的开源 Llama 发布，所以本期不收录。

## 矩阵

| 模型 | SGLang | vLLM | TrnRT | vLLM-Omni | DeepInfer |
|---|---|---|---|---|---|
| DeepSeek-V4.1-Flash-1017 | ✅ [cookbook](https://docs.sglang.io/cookbook/autoregressive/DeepSeek/DeepSeek-V4_1) | ✅ [recipe](https://recipes.vllm.ai/deepseek-ai/DeepSeek-V4.1-Flash) | ❌ | ➖ | ✅ [README](https://github.com/deepseek-ai/DeepInfer#readme)（唯一支持的模型） |
| DeepSeek-V4-Pro-0813 | ✅ [cookbook](https://docs.sglang.io/cookbook/autoregressive/DeepSeek/DeepSeek-V4) | ✅ [recipe](https://recipes.vllm.ai/deepseek-ai/DeepSeek-V4-Pro) | ❌ | ➖ | ❌ |
| Qwen3.8-2.4T-A95B | ✅ [cookbook](https://docs.sglang.io/cookbook/autoregressive/Qwen/Qwen3.8) | ✅ [recipe](https://recipes.vllm.ai/Qwen/Qwen3.8-2.4T-A95B)（仅 B300/GB300） | ❌ | ➖ | ❌ |
| Qwen3.8-27B | ✅ [cookbook](https://docs.sglang.io/cookbook/autoregressive/Qwen/Qwen3.8-27B) | ✅ [recipe](https://recipes.vllm.ai/Qwen/Qwen3.8-27B) | ❌ | ➖ | ❌ |
| GLM-5.3 | ✅ [cookbook](https://docs.sglang.io/cookbook/autoregressive/GLM/GLM-5.3) | ✅ [recipe](https://recipes.vllm.ai/zai-org/GLM-5.3) | ❌ | ➖ | ❌ |
| GLM-5.3-Flash | ✅ [cookbook](https://docs.sglang.io/cookbook/autoregressive/GLM/GLM-5.3-Flash) | ✅ [recipe](https://recipes.vllm.ai/zai-org/GLM-5.3-Flash) | ✅ [README](https://github.com/RunanywhereAI/trnrt#supported-hardware-and-models)（trn2.48xlarge） | ➖ | ❌ |
| Kimi-K3.1-Pro | ✅ [cookbook](https://docs.sglang.io/cookbook/autoregressive/Moonshotai/Kimi-K3.1-Pro)（NVIDIA B300 标为 in-progress） | ✅ [recipe](https://recipes.vllm.ai/moonshotai/Kimi-K3.1-Pro)（无 H100/H200/B200 单机配置） | ❌ | ➖ | ❌ |
| MiniMax-M3.1-Flash | ✅ [cookbook](https://docs.sglang.io/cookbook/autoregressive/MiniMax/MiniMax-M3.1) | ✅ [recipe](https://recipes.vllm.ai/MiniMaxAI/MiniMax-M3.1-Flash) | ❌ | ➖ | ❌ |
| gpt-oss-120b | ✅ [cookbook](https://docs.sglang.io/cookbook/autoregressive/OpenAI/GPT-OSS) | ✅ [recipe](https://recipes.vllm.ai/openai/gpt-oss-120b) | ❌ | ➖ | ❌ |
| Mistral-Large-4-1T-A52B | ✅ [cookbook](https://docs.sglang.io/cookbook/autoregressive/Mistral/Mistral-Large-4)（B300 / Vera Rubin） | ✅ [recipe](https://recipes.vllm.ai/mistralai/Mistral-Large-4-1T-A52B) | ❌ | ➖ | ❌ |
| Qwen3-Omni-30B-A3B-Instruct | 🟡 [仅 Thinker](https://docs.sglang.io/docs/supported-models/multimodal_language_models)：多模态理解、文本输出，Talker（语音生成）未支持 | 🟡 [仅 Thinker](https://docs.vllm.ai/en/latest/models/supported_models/)（`Qwen3OmniMoeThinkerForConditionalGeneration`，文本输出） | ❌ | ✅ [recipe](https://github.com/vllm-project/vllm-omni/blob/main/recipes/Qwen/Qwen3-Omni.md)（Thinker+Talker+Code2Wav，文本+语音输出） | ❌ |

### 单元格判定说明

- **SGLang ✅**：`docs/cookbook/autoregressive/` 下有该模型页面，且 `python/sglang/cli/_commands/` 有对应的生成命令。cookbook 对每个「机型 × 策略」标了 `verified / in-progress / unverified`，具体状态写在 [`practice/sglang.md`](practice/sglang.md) 每条命令上。
- **vLLM ✅**：[vLLM Recipes](https://recipes.vllm.ai/) 有该模型页面，并且架构名已在 `vllm/model_executor/models/registry.py` 注册。recipe 只给出部分机型的命令；哪些机型有命令见 [`practice/vllm.md`](practice/vllm.md)。
- **TrnRT**：v0.2.0 README 只列 GLM-5.3-Flash 一个模型，其他模型标为「coming soon」，因此其余记 ❌。
- **vLLM-Omni ➖**：它面向 omni / TTS / 扩散 / 动作模型（见 [supported models](https://vllm-omni.readthedocs.io/en/latest/models/supported_models/)）。纯文本输出的 LLM 应该直接用上游 vLLM，所以记「不适用」。
- **DeepInfer**：本次开源版 README 只列 DeepSeek-V4.1-Flash（默认权重 `DeepSeek-V4.1-Flash-1017`），其余记 ❌。另外它**只提供离线推理**（`deepinfer/entrypoints/llm.py`），不带 HTTP/OpenAI 服务，KV cache 系统、PD 分离和负载均衡都不在开源范围内。

## ⚠ 许可证要点（转述，以原文为准）

| 模型 | 要点 |
|---|---|
| DeepSeek V4.1-Flash / V4-Pro | MIT，代码与权重都可商用 |
| Qwen3.8-27B、gpt-oss-120b、Qwen3-Omni | Apache 2.0 |
| GLM-5.3-Flash | MIT |
| GLM-5.3 | 改版 MIT：经营 MaaS 且集团年营收超过 100 亿美元时需另签授权（[LICENSE](https://huggingface.co/zai-org/GLM-5.3/blob/main/LICENSE)） |
| Qwen3.8-2.4T-A95B | 改版 MIT：产品月活超 1 亿或月营收超 2000 万美元须醒目标注模型名；经营 MaaS / AI 办公助手且 12 个月营收超 5000 万美元须另签授权（[LICENSE](https://huggingface.co/Qwen/Qwen3.8-2.4T-A95B/blob/main/LICENSE)） |
| Kimi-K3.1-Pro | 改版 MIT：经营 MaaS 且 12 个月营收超 2000 万美元须另签协议；月活超 1 亿或月营收超 2000 万美元须标注「Kimi K3.1-Pro」；纯内部使用不受这两条限制（[LICENSE](https://huggingface.co/moonshotai/Kimi-K3.1-Pro/blob/main/LICENSE)） |
| MiniMax-M3.1-Flash | 默认只授权非商业用途；商用须标注「Built with MiniMax M3.1-Flash」，相关产品营收超 2000 万美元须事先书面授权（[LICENSE](https://huggingface.co/MiniMaxAI/MiniMax-M3.1-Flash/blob/main/LICENSE)） |
| Mistral-Large-4 | 改版 MIT：经营 MaaS 业务须另签商业授权（[LICENSE](https://huggingface.co/mistralai/Mistral-Large-4-1T-A52B/blob/main/LICENSE)） |

本仓库的代码与文档为 MIT 许可，**不包含也不再分发任何模型权重**。
