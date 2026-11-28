# OSS LLM Models Lab

> 🤖 **AI task worker / agent：动手前先读 [`AGENTS.md`](AGENTS.md)**，里面是本仓库的事实核对规则、文档约定和成本纪律。

[oss-image-models-lab](https://github.com/liangruibupt/oss-image-models-lab) 的 LLM 姊妹仓库。回答三个问题：

1. 当前主流**开源权重 LLM**，在各个常用**推理框架**里是否受支持？
2. 在 AWS 上**怎么跑**（官方启动命令 + 示例请求）？
3. **性能**如何？先汇总已公布的数据，再用统一的压测工具实测。

> ⚠ **范围**：调研 + 文档 + 压测工具；目前只实测了 **Qwen3.8-27B-FP8 on g6e.xlarge**（vLLM vs SGLang，见 [📊 实测结果](#-实测结果)），其余性能数字都来自公开资料。其他行的实测计划和成本见 [`docs/BENCH_PLAN.md`](docs/BENCH_PLAN.md)，需单独审批。所有支持状态 **checked 2026-11-27**。

---

## 🧰 推理框架

| 框架 | 定位 | 硬件 | 许可证 | 本仓库文档 |
|---|---|---|---|---|
| [SGLang](https://github.com/sgl-project/sglang) | 通用 LLM / VLM 服务，Cookbook 按模型×硬件给命令 | NVIDIA、AMD、TPU、Intel、昇腾等 | Apache 2.0 | [实践](docs/practice/sglang.md) |
| [vLLM](https://github.com/vllm-project/vllm) | 通用 LLM 服务，Recipes 按模型×硬件给命令 | NVIDIA、AMD、Intel、CPU；插件支持 TPU、昇腾、Neuron 等 | Apache 2.0 | [实践](docs/practice/vllm.md) |
| [TrnRT](https://github.com/RunanywhereAI/trnrt) | AWS Trainium2 专用 LLM 引擎（RunAnywhere），OpenAI 兼容 API | 仅 `trn2.48xlarge` | Apache 2.0 | [实践](docs/practice/trnrt.md) |
| [vLLM-Omni](https://github.com/vllm-project/vllm-omni) | omni 模态（any-to-any）模型服务 | CUDA、ROCm、NPU、XPU、MUSA | Apache 2.0 | [实践](docs/practice/vllm-omni.md) |
| [DeepInfer](https://github.com/deepseek-ai/DeepInfer) | DeepSeek 生产推理框架，2026-10-20 开源，**仅离线推理** | NVIDIA SM100、昇腾 950 | Apache 2.0 | [实践](docs/practice/deepinfer.md) |

各框架的并行方式、PD 分离、量化、投机解码/MTP、API 对比见 **[`docs/FRAMEWORKS.md`](docs/FRAMEWORKS.md)**。

## 📊 支持矩阵（摘要）

✅ 官方支持 · 🟡 部分/实验 · ❌ 不支持 · ➖ 不适用。每个单元格的来源链接与判定说明见 **[`docs/SUPPORT_MATRIX.md`](docs/SUPPORT_MATRIX.md)**。

| 模型 | 总参 / 激活 | SGLang | vLLM | TrnRT | vLLM-Omni | DeepInfer |
|---|---|---|---|---|---|---|
| [DeepSeek-V4.1-Flash-1017](https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash-1017) | 552B（+196B Engram）/ 8–16B | ✅ | ✅ | ❌ | ➖ | ✅ |
| [DeepSeek-V4-Pro-0813](https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro-0813) | 1.6T / 49B | ✅ | ✅ | ❌ | ➖ | ❌ |
| [Qwen3.8-2.4T-A95B](https://huggingface.co/Qwen/Qwen3.8-2.4T-A95B) | 2.4T / 95B | ✅ | ✅ | ❌ | ➖ | ❌ |
| [Qwen3.8-27B](https://huggingface.co/Qwen/Qwen3.8-27B) | 27B dense | ✅ | ✅ | ❌ | ➖ | ❌ |
| [GLM-5.3](https://huggingface.co/zai-org/GLM-5.3) | ~753B | ✅ | ✅ | ❌ | ➖ | ❌ |
| [GLM-5.3-Flash](https://huggingface.co/zai-org/GLM-5.3-Flash) | 320B / 18B | ✅ | ✅ | ✅ | ➖ | ❌ |
| [Kimi-K3.1-Pro](https://huggingface.co/moonshotai/Kimi-K3.1-Pro) | 2.8T / 104B | ✅ | ✅ | ❌ | ➖ | ❌ |
| [MiniMax-M3.1-Flash](https://huggingface.co/MiniMaxAI/MiniMax-M3.1-Flash) | ~428B / 23B | ✅ | ✅ | ❌ | ➖ | ❌ |
| [gpt-oss-120b](https://huggingface.co/openai/gpt-oss-120b) | 117B / 5.1B | ✅ | ✅ | ❌ | ➖ | ❌ |
| [Mistral-Large-4-1T-A52B](https://huggingface.co/mistralai/Mistral-Large-4-1T-A52B) | ~1T / 52B | ✅ | ✅ | ❌ | ➖ | ❌ |
| [Qwen3-Omni-30B-A3B-Instruct](https://huggingface.co/Qwen/Qwen3-Omni-30B-A3B-Instruct) | 30B / 3B | 🟡 仅 Thinker | 🟡 仅 Thinker | ❌ | ✅ | ❌ |

一句话：**SGLang 和 vLLM 覆盖了全部 10 个文本 LLM**；TrnRT 只支持 GLM-5.3-Flash，DeepInfer 只支持 DeepSeek-V4.1-Flash；要 Qwen3-Omni 的语音输出只能用 vLLM-Omni。

## 📊 实测结果

本仓库在 AWS 上实测的组合与进度。实测预算按行单独审批，计划与成本见 [`docs/BENCH_PLAN.md`](docs/BENCH_PLAN.md)。

| 优先级 | 模型 | 框架 | 实例 | 状态 |
|---|---|---|---|---|
| P0 | gpt-oss-120b | vLLM + SGLang | `p5.48xlarge` | ⏳ [待补充](docs/results/gpt-oss-120b_p5.md) |
| P0 | Qwen3.8-27B-FP8 | vLLM + SGLang | `g6e.xlarge` | ✅ [已实测](docs/results/qwen3.8-27b_g6e.md)（ap-northeast-1） |
| P0 | Qwen3-Omni-30B-A3B-Instruct | vLLM-Omni | `p5.48xlarge` | ⏳ [待补充](docs/results/qwen3-omni-30b-a3b_p5.md) |
| P0 | GLM-5.3-Flash | vLLM + SGLang | `p5.48xlarge` | ⏳ [待补充](docs/results/glm-5.3-flash_p5.md) |
| P0 | GLM-5.3-Flash | TrnRT | `m7i.16xlarge`（编译）+ `trn2.48xlarge` | ⏳ [待补充](docs/results/glm-5.3-flash_trn2.md) |
| P0 | DeepSeek-V4.1-Flash-1017 | vLLM + SGLang | `p5en.48xlarge` | ⏳ [待补充](docs/results/deepseek-v4.1-flash_p5en.md) |
| P1 | DeepSeek-V4.1-Flash-1017 | DeepInfer | `p6-b200.48xlarge` | ⏳ [待补充](docs/results/deepseek-v4.1-flash_p6-b200_deepinfer.md) |
| P1 | GLM-5.3 | vLLM + SGLang | `p5en.48xlarge` | ⏳ [待补充](docs/results/glm-5.3_p5en.md) |
| P1 | DeepSeek-V4-Pro-0813 | vLLM + SGLang | `p5en.48xlarge` | ⏳ [待补充](docs/results/deepseek-v4-pro-0813_p5en.md) |
| P1 | MiniMax-M3.1-Flash | SGLang | `p5en.48xlarge` | ⏳ [待补充](docs/results/minimax-m3.1-flash_p5en.md) |
| P2 | MiniMax-M3.1-Flash | vLLM + SGLang | `p6-b300.48xlarge` | ⏳ [待补充](docs/results/minimax-m3.1-flash_p6-b300.md) |
| P2 | Mistral-Large-4-1T-A52B | vLLM + SGLang | `p6-b300.48xlarge` | ⏳ [待补充](docs/results/mistral-large-4_p6-b300.md) |
| P2 | Qwen3.8-2.4T-A95B（NVFP4） | SGLang | `p6-b300.48xlarge` | ⏳ [待补充](docs/results/qwen3.8-2.4t-a95b_p6-b300.md) |

### 如何补充你的结果

1. 打开该行的占位文档（`docs/results/<model>_<instance>.md`，模板 [`docs/results/TEMPLATE.md`](docs/results/TEMPLATE.md)），按其中的启动命令起服务（有改动写明）。
2. 在同一台实例上跑文档里的两条 `bench/llm_bench.py` 命令（W1 1024/256、W2 8192/1024，并发 1/8/32/64），`--out` 指向 `results/<model>_<instance>/<框架>_w1_1024_256` 等，生成 `.json` + `.md`。
3. 把 JSON/MD 提交到 `results/<model>_<instance>/`，把数字填进占位文档的结果表，补齐版本、日期、运行者、实际成本，并把状态行改为 ✅。
4. 把本表（README 与 [`docs/BENCH_PLAN.md`](docs/BENCH_PLAN.md) 各一份）对应行改为 `✅ 已实测`，走 feature 分支 + PR。
5. 跑完立刻终止实例：`python scripts/teardown.py --name <Name tag>`，再用 `aws ec2 describe-instances` 确认 `terminated`。

## 📚 文档索引

| 文档 | 内容 |
|---|---|
| [`docs/FRAMEWORKS.md`](docs/FRAMEWORKS.md) | 每个框架是什么、硬件（GPU / Trainium / 昇腾）、TP/PP/EP/DP、PD 分离、量化、投机解码/MTP、API、许可证 |
| [`docs/SUPPORT_MATRIX.md`](docs/SUPPORT_MATRIX.md) | 模型清单（参数、上下文、许可证）+ 完整矩阵 + 每格来源 + 许可证要点 |
| [`docs/practice/sglang.md`](docs/practice/sglang.md) | SGLang：各 ✅ 组合在 p5 / p5en / p6-b200 / p6-b300 上的启动命令与示例请求 |
| [`docs/practice/vllm.md`](docs/practice/vllm.md) | vLLM：同上 |
| [`docs/practice/trnrt.md`](docs/practice/trnrt.md) | TrnRT：GLM-5.3-Flash 的编译缓存构建 + trn2.48xlarge 服务 |
| [`docs/practice/vllm-omni.md`](docs/practice/vllm-omni.md) | vLLM-Omni：Qwen3-Omni 三 stage 部署与文本/语音输出 |
| [`docs/practice/deepinfer.md`](docs/practice/deepinfer.md) | DeepInfer：构建、离线推理与自带基准 |
| [`docs/PERF_PUBLISHED.md`](docs/PERF_PUBLISHED.md) | 已公布的性能数据，逐条标注官方/第三方、硬件、精度、负载 |
| [`docs/hardware/deepseek-v4.1-flash_h20_rtx6000d.md`](docs/hardware/deepseek-v4.1-flash_h20_rtx6000d.md) | DeepSeek-V4.1-Flash 在 H20 / H20-3e / RTX PRO 6000D 上的可行性与公开 benchmark |
| [`docs/BENCH_PLAN.md`](docs/BENCH_PLAN.md) | 建议的实测组合、预估时长与按需成本（逐行审批） |
| [`docs/results/`](docs/results/) | 实测结果：[Qwen3.8-27B · g6e.xlarge](docs/results/qwen3.8-27b_g6e.md)（✅）及其余各行的占位文档（⏳，[模板](docs/results/TEMPLATE.md)） |
| [`scripts/`](scripts/) | `launch.py` / `teardown.py`（boto3，自有 Name tag、key、SG）与实例上运行的 `box/*.sh` |
| [`bench/README.md`](bench/README.md) | 框架无关的 OpenAI 兼容压测工具（TTFT / TPOT / ITL / 吞吐） |
| [`AGENTS.md`](AGENTS.md) | 给后续 agent 的首读指引 |

## ⏱ 压测工具（TL;DR）

```bash
# 本地单元测试（不需要 GPU）
python3 -m unittest discover -s bench -v

# 对任意 OpenAI 兼容端点压测
python bench/llm_bench.py --base-url http://127.0.0.1:8000/v1 --model <served-model> \
  --input-len 1024 --output-len 256 --concurrency 1,8,32,64 --out results/<run-name>
```

## ⚠ 许可证提醒

本仓库代码与文档为 MIT（见 [`LICENSE`](LICENSE)），**不包含任何模型权重**。各模型许可证差别很大：DeepSeek、GLM-5.3-Flash 为 MIT；Qwen3.8-27B、gpt-oss、Qwen3-Omni 为 Apache 2.0；GLM-5.3、Qwen3.8-2.4T、Kimi-K3.1-Pro、Mistral-Large-4 是带营收 / MaaS 条款的改版 MIT；**MiniMax-M3.1-Flash 默认只授权非商业用途**。商用前请读原文，摘要见 [`docs/SUPPORT_MATRIX.md`](docs/SUPPORT_MATRIX.md#-许可证要点转述以原文为准)。

## 仓库结构

```
oss-llm-models-lab/
├── README.md                 # 本文件
├── AGENTS.md                 # 给 AI agent 的首读指引
├── LICENSE                   # MIT（仅代码与文档）
├── .github/workflows/
│   └── gitleaks.yml          # 密钥扫描
├── scripts/                  # launch.py / teardown.py / make_placeholders.py / box/*.sh
├── results/                  # 实测原始 JSON + markdown（每行一个目录）
├── bench/
│   ├── README.md             # 压测工具说明
│   ├── llm_bench.py          # 压测主程序（标准库，无依赖）
│   ├── mock_server.py        # 本地 mock OpenAI 服务
│   ├── test_llm_bench.py     # 单元测试
│   └── sample/               # 对 mock 服务跑出的示例输出
└── docs/
    ├── FRAMEWORKS.md
    ├── SUPPORT_MATRIX.md
    ├── PERF_PUBLISHED.md
    ├── BENCH_PLAN.md
    ├── hardware/             # 非 AWS 机型（H20、RTX PRO 6000D 等）的可行性与公开数据
    ├── results/              # 实测结果文档 + TEMPLATE.md + 占位文档
    └── practice/
        ├── sglang.md
        ├── vllm.md
        ├── trnrt.md
        ├── vllm-omni.md
        └── deepinfer.md
```
