# 🧰 推理框架速览

> **checked 2026-11-27**。信息来自各项目 README、官方文档与源码（提交号见 [`SUPPORT_MATRIX.md`](SUPPORT_MATRIX.md)）。表中「—」表示官方文档没有提到。

## 总览

| | SGLang | vLLM | TrnRT | vLLM-Omni | DeepInfer |
|---|---|---|---|---|---|
| 仓库 | [sgl-project/sglang](https://github.com/sgl-project/sglang) | [vllm-project/vllm](https://github.com/vllm-project/vllm) | [RunanywhereAI/trnrt](https://github.com/RunanywhereAI/trnrt) | [vllm-project/vllm-omni](https://github.com/vllm-project/vllm-omni) | [deepseek-ai/DeepInfer](https://github.com/deepseek-ai/DeepInfer) |
| 最新版本（2026-11-27） | v0.5.23（2026-11-02） | v0.34.0（2026-11-16） | v0.2.0（2026-11-25） | v0.34.0（2026-11-22） | 无 release，首次提交 2026-10-20 |
| 许可证 | Apache 2.0 | Apache 2.0 | Apache 2.0 | Apache 2.0 | Apache 2.0 |
| 定位 | 通用 LLM / VLM / 扩散服务 | 通用 LLM 服务 | AWS Trainium2 专用 LLM 引擎 | omni 模态（文/图/音/视频/动作）服务 | DeepSeek 自家生产推理框架（开源离线部分） |
| 硬件 | NVIDIA、AMD、Google TPU、Intel GPU/CPU、Apple Silicon、华为昇腾、摩尔线程 | NVIDIA、AMD、Intel GPU、x86/ARM/PowerPC CPU；插件支持 TPU、Gaudi、昇腾、AWS Neuron 等 | 仅 trn2.48xlarge | CUDA、ROCm、NPU、XPU、MUSA | NVIDIA SM100（B200 级）、华为昇腾 950 |
| 并行 | TP / PP / EP / DP-attention / CP | TP / PP / DP / EP / CP | 每引擎 TP32（32 个逻辑 NeuronCore），每台 2 个引擎 | TP / PP / DP / EP | Attention DP、均衡 CP、MoE EP + EPLB |
| PD 分离 | ✔（PD 与 EPD 分离） | ✔（prefill / decode / encode 分离） | — | ✔（OmniConnector 跨 stage 分离） | 引擎侧大部分已实现，但 VE/P/D 分离组件**未开源** |
| 量化 | FP8、MXFP8、MXFP4、NVFP4、INT8/INT4、AWQ、GPTQ、W8A8/W4A8、GGUF、ModelOpt | FP8、MXFP8/MXFP4、NVFP4、INT8、INT4、GPTQ/AWQ、GGUF、compressed-tensors、ModelOpt、TorchAO | FP8 权重与 FP8 KV 页 | 继承 vLLM，另有扩散模型量化 | 使用模型原生 FP4/FP8 混合权重 |
| 投机解码 / MTP | EAGLE / EAGLE-3、DFlash、DSpark、MTP/NEXTN、n-gram、standalone | n-gram、suffix、EAGLE、DFlash；DSpark（DeepSeek V4/V4.1 recipe） | 模型自带 MTP 层（每步 2 个 draft），仅 `latency` 构建 | 继承 vLLM | DSpark + 置信度调度的变长验证 |
| API | OpenAI 兼容、原生 `/generate` | OpenAI 兼容、Anthropic Messages、gRPC | OpenAI chat/completions/Responses、Anthropic Messages、原生 `/generate` | OpenAI 兼容、全双工实时接口 | **仅离线 Python API**（`LLM`），无 HTTP 服务 |

## SGLang

- **是什么**：高性能 LLM 与多模态模型服务框架（[README](https://github.com/sgl-project/sglang#readme)）。按「模型 × 硬件」给出现成启动命令的 [Cookbook](https://docs.sglang.io/cookbook/autoregressive/intro) 是本仓库 practice 文档的主要来源。
- **硬件**：README 的支持表列出 NVIDIA（B200/B300/GB200/GB300、H100/H200/H20、A100、RTX 系列等）、AMD Instinct MI300X–MI355X、Google TPU（v6e、v7）、Intel Arc / Xeon、Apple Silicon、华为昇腾 A2/A3/950PR/DT、摩尔线程 MTT S5000。
- **并行与 PD**：文档有 [expert parallelism](https://docs.sglang.io/docs/advanced_features/expert_parallelism)、[pipeline parallelism](https://docs.sglang.io/docs/advanced_features/pipeline_parallelism)、[PD disaggregation](https://docs.sglang.io/docs/advanced_features/pd_disaggregation)、EPD（vision encoder / prefill / decode）分离和 DP-attention 路由。
- **量化**：见 [quantization](https://docs.sglang.io/docs/advanced_features/quantization)。
- **投机解码**：见 [speculative decoding](https://docs.sglang.io/docs/advanced_features/speculative_decoding)；DeepSeek V4 正式版、Mistral Large 4、Qwen3.8 的 cookbook 用 DSpark。
- **API**：OpenAI 兼容服务，默认端口 30000。

## vLLM

- **是什么**：高吞吐、省显存的 LLM 推理与服务引擎（[README](https://github.com/vllm-project/vllm#readme)）。社区维护的 [vLLM Recipes](https://recipes.vllm.ai/) 按「模型 × 硬件 × 并行策略」生成命令，并提供 JSON API（`/{hf_id}/hw/{hw}.json`），本仓库的 vLLM 命令就从这个 API 取。
- **硬件**：NVIDIA、AMD、Intel GPU、x86/ARM/PowerPC CPU；通过硬件插件支持 Google TPU、Intel Gaudi、IBM Spyre、华为昇腾、Apple Silicon 等。AWS Trainium/Inferentia 有社区维护的插件 [vllm-project/vllm-neuron](https://github.com/vllm-project/vllm-neuron)（本仓库未核对它对矩阵中模型的支持）。
- **并行与 PD**：README 列出 tensor / pipeline / data / expert / context parallelism，以及 prefill、decode、encode 分离。
- **量化**：见 [quantization 文档](https://docs.vllm.ai/en/latest/features/quantization/index.html)。
- **投机解码**：n-gram、suffix、EAGLE、DFlash；DeepSeek V4/V4.1 recipe 通过 `--speculative-config '{"method":"dspark",...}'` 启用 DSpark。
- **API**：OpenAI 兼容服务、Anthropic Messages API、gRPC，默认端口 8000。

## TrnRT（RunAnywhere）

- **是什么**：面向 AWS Trainium 的开源 LLM 推理引擎。在一台 `trn2.48xlarge` 上提供 OpenAI 兼容 API；decode 用 NKI megakernel 实现（大约每半层一个 kernel）；前缀缓存跨设备与主机内存（[README](https://github.com/RunanywhereAI/trnrt#readme)，[博客](https://runanywhere.ai/blog/glm-5-3-flash-trainium2-nki-megakernels)）。
- **模型**：只支持 GLM-5.3-Flash（FP8，1M 上下文），README 称更多模型「coming soon」。
- **硬件**：trn2.48xlarge（16 颗 Trainium2，每颗 96 GiB HBM，LNC 2），Neuron SDK 2.32。编译缓存在任意 x86_64 主机上离线构建（不需要 NeuronCore，耗时数小时），服务机只加载编译结果（[DEPLOY.md](https://github.com/RunanywhereAI/trnrt/blob/development/docs/DEPLOY.md)）。
- **并行**：每台 2 个引擎，每个引擎在 32 个逻辑 NeuronCore 上做 TP，前面是按 session 亲和的路由器。没有提到 PD 分离或多机。
- **构建档位**：`latency` / `balanced`（默认）/ `throughput`，按每个引擎的并发用户数选，`--preset auto --users N` 可自动选（[CONFIGURATION.md](https://github.com/RunanywhereAI/trnrt/blob/development/docs/CONFIGURATION.md)）。
- **投机解码**：用模型自带的 MTP 层，每步 2 个 draft，只有 `latency` 构建开启。
- **API**：OpenAI chat / completions / Responses、Anthropic Messages、原生 `/generate` 与 `/tokenize`，支持流式、tool call、reasoning 输出、xgrammar 结构化输出（[API.md](https://github.com/RunanywhereAI/trnrt/blob/development/docs/API.md)）。
- **注意**：README 的基准数据是用早于 v0.2.0 的内部构建测的；v0.2.0 本身的设备端运行在 README 中标为「pending」。

## vLLM-Omni

- **是什么**：把 vLLM 扩展到 omni 模态（文本、图像、音频、视频、动作）与非自回归架构（DiT 等）的服务框架（[README](https://github.com/vllm-project/vllm-omni#readme)，[文档](https://vllm-omni.readthedocs.io/en/latest/)）。
- **模型**：Qwen3-Omni、MiniCPM-o 4.5、TTS、扩散（图像/视频/音频）、机器人策略模型等（[supported models](https://vllm-omni.readthedocs.io/en/latest/models/supported_models/)）。纯文本 LLM 不在它的范围内，应直接用 vLLM。
- **硬件**：release 说明覆盖 CUDA、ROCm、MUSA、NPU、XPU。
- **并行与分离**：README 列出 tensor / pipeline / data / expert parallelism；基于 OmniConnector 的全分离部署和跨 stage 动态资源分配。Qwen3-Omni 默认拆成 Thinker / Talker / Code2Wav 三个 stage，默认部署配置用 2 张卡（[deploy config](https://github.com/vllm-project/vllm-omni/blob/main/vllm_omni/deploy/qwen3_omni_moe.yaml)）。
- **API**：OpenAI 兼容服务（启动时加 `--omni`），可用 `modalities` 选择输出文本/语音；另有全双工实时接口。

## DeepInfer（DeepSeek）

- **是什么**：支撑 DeepSeek 大规模线上服务的推理框架，2026-10-20 首次开源（首个提交日期），Apache 2.0（[README](https://github.com/deepseek-ai/DeepInfer#readme)）。本次开源的是**离线推理**部分。
- **模型**：只支持 DeepSeek-V4.1-Flash（默认权重 `deepseek-ai/DeepSeek-V4.1-Flash-1017`）。
- **硬件**：NVIDIA SM100 GPU（CUDA 13）与华为昇腾 950（CANN 9.2）；需从源码构建（GCC ≥ 13、Python 3.12）。
- **并行**：Attention DP / 均衡 CP、MoE EP + EPLB。官方 [部署 Q&A](https://github.com/deepseek-ai/DeepInfer/blob/main/doc/inference_deployment_qa.md) 的生产配置是 prefill EP2–8 / DP2–8、decode EP64–128（Wide-EP），暂不用 TP 和 CP。
- **最小高效部署单元**：同一份 Q&A 说 1P+1D 即可部署，P:D 的 GPU 比例约 1:1；由于 decode 建议 EP64 以上，最小高效单元是 **64 张 prefill GPU + 64 张 decode GPU（共 128 张）**。
- **未开源部分**：KV cache 系统、VE/Prefill/Decode 分离（引擎所需功能大部分已实现）、prefill 与 decode 的数据并行负载均衡。所以开源版不能直接对外提供在线服务。
- **其他特性**：FlashMLA / DeepGEMM / DeepEP 等 kernel、DSpark 投机解码与置信度调度验证、SWA bounded replay、异步调度、batch-invariant 推理、确定性采样、结构化输出。
- **API**：Python 离线 `LLM` 接口（`deepinfer/entrypoints/llm.py`），没有 HTTP 服务，因此本仓库的 [`bench/`](../bench/) 不能直接压测它，需要用它自带的 `examples/benchmark.py`。
