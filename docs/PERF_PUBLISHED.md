# 📈 已公布的性能数据（非本仓库实测）

> **checked 2026-11-27**。这里只收录公开发布的数字，每条标明：**来源类型**（官方 = 框架或模型方自己发布；第三方 = 其他机构测得）、来源链接、硬件、精度、负载。**本仓库尚未做任何实测**，实测计划见 [`BENCH_PLAN.md`](BENCH_PLAN.md)。
>
> 不同来源的负载、指标口径和软件版本都不一样，**跨表比较没有意义**。例如 SGLang cookbook 的 tok/s/GPU 是输入+输出合计，DeepInfer 的 decode 吞吐按投机 token 全接受计算。

## 1. SGLang cookbook（官方 · SGLang 团队）

口径：`bench_serving` / `sglang.benchmark.serving`，随机数据集，TTFT 与 TPOT 为中位数，**tok/s/GPU = (输入+输出) 合计吞吐 / GPU 数**。数据取自 cookbook 的基准配置文件 `docs/src/snippets/configs/<org>/<model>-benchmarks.jsx`（sglang@`f8fd250`）。

### GLM-5.3（[cookbook](https://docs.sglang.io/cookbook/autoregressive/GLM/GLM-5.3)）· FP8 · 单机 8 卡 · ISL 8192 / OSL 1024 · SGLang main@`20a491d1d311`

| 硬件 | 策略 | 并发 | TTFT (ms) | TPOT (ms) | tok/s/GPU |
|---|---|---:|---:|---:|---:|
| 8×H200 | low-latency | 1 | 780 | 3.71 | 252 |
| 8×H200 | low-latency | 16 | 5499 | 14.20 | 920 |
| 8×H200 | high-throughput | 64 | 7790 | 21.90 | 2440 |
| 8×H200 | high-throughput | 256 | 57607 | 33.39 | 2558 |
| 8×B200 | low-latency | 1 | 400 | 3.11 | 321 |
| 8×B200 | high-throughput | 64 | 5908 | 16.53 | 3220 |
| 8×B200 | high-throughput | 256 | 18916 | 31.88 | 5025 |
| 8×B300 | low-latency | 1 | 342 | 3.10 | 328 |
| 8×B300 | high-throughput | 64 | 5586 | 16.37 | 3296 |
| 8×B300 | high-throughput | 256 | 17848 | 32.48 | 5259 |

### DeepSeek-V4-Pro（[cookbook](https://docs.sglang.io/cookbook/autoregressive/DeepSeek/DeepSeek-V4)）· FP4 · 单机 8 卡 · ISL 8192 / OSL 1024

注意：这些数据对应 cookbook 的 `pro` 变体，即 **V4-Pro 预览版**权重（`deepseek-ai/DeepSeek-V4-Pro`），不是矩阵里的 0813 正式版；正式版（`pro-official`）在 cookbook 中暂无速度数据。

| 硬件 | SGLang | 策略 | 并发 | TTFT (ms) | TPOT (ms) | tok/s/GPU |
|---|---|---|---:|---:|---:|---:|
| 8×H200 | 0.5.15.post1 | low-latency | 1 | 634 | 5.65 | 170 |
| 8×H200 | 0.5.15.post1 | balanced | 64 | 41506 | 26.14 | 589 |
| 8×B200 | 0.5.15 | low-latency | 1 | 230 | 4.25 | 243 |
| 8×B200 | 0.5.15 | balanced | 64 | 1081 | 36.23 | 1696 |
| 8×B200 | 0.5.15 | high-throughput | 1024 | 107158 | 44.45 | 4169 |
| 8×B300 | 0.5.15.post1 | low-latency | 1 | 258 | 4.2 | 243 |
| 8×B300 | 0.5.15.post1 | balanced | 64 | 1868 | 42.19 | 1336 |
| 8×B300 | 0.5.15.post1 | high-throughput | 4096 | 257656 | 42.13 | 4400 |

### Mistral Large 4（[cookbook](https://docs.sglang.io/cookbook/autoregressive/Mistral/Mistral-Large-4)）· FP8 · 8×B300 TP8 · ISL 1024 / OSL 512 · 镜像 `lmsysorg/sglang:mistral-large-4`

| 策略 | 并发 | TTFT (ms) | TPOT (ms) | tok/s/GPU |
|---|---:|---:|---:|---:|
| high-throughput（无投机） | 1 | 72.7 | 10.49 | 35.4 |
| high-throughput（无投机） | 64 | 1306.9 | 28.42 | 774.1 |
| low-latency（DSpark） | 1 | 77.4 | 3.85 | 90.6 |
| low-latency（DSpark） | 64 | 1348.6 | 9.81 | 1017.6 |

cookbook 还给出 4×GB300 NVFP4 在并发 64 时 1,560（无投机）与 2,812（DSpark）tok/s/GPU。

### MiniMax-M3（[cookbook](https://docs.sglang.io/cookbook/autoregressive/MiniMax/MiniMax-M3)）· ISL 2048 / OSL 256 · 并发 64 · SGLang v0.5.23

矩阵里的 M3.1-Flash 暂无公布的速度数据；下面是同架构、同参数规模的 M3（约 428B / 23B），仅供量级参考。

| 硬件 | 精度 | TTFT (ms) | TPOT (ms) | tok/s/GPU |
|---|---|---:|---:|---:|
| H200（单机） | BF16 | 888 | 41.8 | 1381 |
| B200（单机） | MXFP8 | 413 | 25.6 | 2261 |
| B300（单机） | MXFP8 | 446 | 31.5 | 3703 |

### gpt-oss-120b（[cookbook §5](https://docs.sglang.io/cookbook/autoregressive/OpenAI/GPT-OSS)）· 8×B200 TP8 · SGLang 0.5.6 · ShareGPT 数据集，100 个请求

| 场景 | 并发 | 平均 TTFT (ms) | 平均 TPOT (ms) | 输出 tok/s（整机） |
|---|---:|---:|---:|---:|
| latency-sensitive | 1 | 33.71 | 2.31 | 405.93 |

## 2. TrnRT（官方 · RunAnywhere，框架作者自测）

来源：[TrnRT README](https://github.com/RunanywhereAI/trnrt#benchmarks) 与 [docs/RESULTS.md](https://github.com/RunanywhereAI/trnrt/blob/development/docs/RESULTS.md)。模型 GLM-5.3-Flash FP8，1 台 `trn2.48xlarge`，[SemiAnalysis AgentX](https://github.com/SemiAnalysisAI/agentx-harness)（回放真实 coding-agent 会话），1M 上下文，32 个并发 agent，每个点跑 1 小时。**用的是早于 v0.2.0 的内部构建**（v0.1.0 的 batch preset）。

| Decode batch | 请求/分钟 | Token/分钟（输入含缓存+输出） | 每用户 decode tok/s（p50） | 首 token（缓存命中，p50） | $/M tokens（spot） |
|---:|---:|---:|---:|---:|---:|
| 4 | 19.3 | 2.36M | 46.6 | 76.73 s | $0.061 |
| 8 | 25.2 | 3.02M | 29.4 | 28.82 s | $0.047 |
| 12（默认） | 28.9 | 3.57M | 22.3 | 6.53 s | $0.040 |

spot 价 $8.60/h（us-east-2，2026-11-03，README 原文）；按 Capacity Block $35.76/h 计，batch 12 为 $0.167/M tokens。

README 另有 InferenceX AgentX 下与 GPU 的对比（同一模型 FP8，按 AWS Capacity Block 价格算每美元 token 数）。其中 H100/H200 数据是 **InferenceX 公开运行的第三方数据**，TrnRT 作者说明未核验其准确率：

| 并发用户 | 每美元 token：trn2 ÷ H200 | 每美元 token：trn2 ÷ H100 | P90 交互速度 tok/s/用户：trn2 / H200 |
|---:|---:|---:|---:|
| 1 | 1.64× | 1.52× | 62.2 / 272 |
| 8 | 1.61× | 2.01× | 25.8 / 168 |
| 16 | 1.07× | 3.82× | 14.2 / 87.8 |
| 32 | 0.81× | 4.95× | 10.7 / 50.1 |

对比单位是 1 个 TrnRT 引擎（8 颗 Trainium2，即半台 trn2.48xlarge）对 1 台 8 卡 GPU 节点；1–8 用户的点用 InferenceX 规定的 MTP 接受长度 2.519（trn2 实测为 2.20）。README 同时说明：在无前缀复用的 8K/1K 定长负载上，trn2 每美元 token 只有 H200 的 0.56–0.76 倍。

## 3. DeepInfer（官方 · DeepSeek）

来源：[部署 Q&A · 投机解码](https://github.com/deepseek-ai/DeepInfer/blob/main/doc/inference_deployment_qa.md#speculative-decoding)。模型 DeepSeek-V4.1-Flash，EP64/DP64 离线基准（README 说明 decode 基准在 64 张 SM100 GPU 上测），Open-PerfectBlend 数据集，**按基准数据推算的每 rank 吞吐**。

| 每 rank 并发序列 | 固定 5 token 验证 tok/s/rank | 动态长度验证 tok/s/rank | 提升 |
|---:|---:|---:|---:|
| 16 | 4891 | 4816 | −1.5% |
| 32 | 8964 | 9111 | +1.6% |
| 60（生产工作点附近） | 13730 | 14466 | +5.4% |
| 96 | 16817 | 18660 | +11.0% |

同一文档称：单个集群每天服务 155 万亿 token，按闲时价格计整体收入为每 GPU 小时 38 美元。README 的 prefill（4 张 SM100）与 decode（64 张 SM100）Pareto 曲线只以图片形式发布（[prefill](https://github.com/deepseek-ai/DeepInfer/blob/main/doc/images/prefill_pareto.png)、[decode](https://github.com/deepseek-ai/DeepInfer/blob/main/doc/images/decode_pareto.png)），这里不转抄数值。

## 4. 暂无公布数据

| 组合 | 状态 |
|---|---|
| vLLM × 全部模型 | vLLM Recipes 页面以启动配置为主，2026-11-27 未找到矩阵模型在 AWS 对应 GPU 上的结构化速度表 |
| SGLang × DeepSeek-V4.1-Flash、Qwen3.8-2.4T、Qwen3.8-27B、GLM-5.3-Flash、Kimi-K3.1-Pro、MiniMax-M3.1-Flash（H/B 系列） | cookbook 基准文件里这些条目为空或只有准确率 |
| vLLM-Omni × Qwen3-Omni | 未找到 |
