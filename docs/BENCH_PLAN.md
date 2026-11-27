# 🧪 实测计划（待成本审批，尚未执行）

> 下面是建议的实测组合、预估时长与按需成本，**每一行需单独审批后再执行**。价格读取于 2026-11-27。目前只有 Qwen3.8-27B-FP8 · g6e.xlarge 一行已实测（ap-northeast-1，见 [📊 实测结果](#-实测结果)）。

## 📊 实测结果

| 优先级 | 模型 | 框架 | 实例 | 状态 |
|---|---|---|---|---|
| P0 | gpt-oss-120b | vLLM + SGLang | `p5.48xlarge` | ⏳ [待补充](results/gpt-oss-120b_p5.md) |
| P0 | Qwen3.8-27B-FP8 | vLLM + SGLang | `g6e.xlarge` | ✅ [已实测](results/qwen3.8-27b_g6e.md)（ap-northeast-1） |
| P0 | Qwen3-Omni-30B-A3B-Instruct | vLLM-Omni | `p5.48xlarge` | ⏳ [待补充](results/qwen3-omni-30b-a3b_p5.md) |
| P0 | GLM-5.3-Flash | vLLM + SGLang | `p5.48xlarge` | ⏳ [待补充](results/glm-5.3-flash_p5.md) |
| P0 | GLM-5.3-Flash | TrnRT | `m7i.16xlarge`（编译）+ `trn2.48xlarge` | ⏳ [待补充](results/glm-5.3-flash_trn2.md) |
| P0 | DeepSeek-V4.1-Flash-1017 | vLLM + SGLang | `p5en.48xlarge` | ⏳ [待补充](results/deepseek-v4.1-flash_p5en.md) |
| P1 | DeepSeek-V4.1-Flash-1017 | DeepInfer | `p6-b200.48xlarge` | ⏳ [待补充](results/deepseek-v4.1-flash_p6-b200_deepinfer.md) |
| P1 | GLM-5.3 | vLLM + SGLang | `p5en.48xlarge` | ⏳ [待补充](results/glm-5.3_p5en.md) |
| P1 | DeepSeek-V4-Pro-0813 | vLLM + SGLang | `p5en.48xlarge` | ⏳ [待补充](results/deepseek-v4-pro-0813_p5en.md) |
| P1 | MiniMax-M3.1-Flash | SGLang | `p5en.48xlarge` | ⏳ [待补充](results/minimax-m3.1-flash_p5en.md) |
| P2 | MiniMax-M3.1-Flash | vLLM + SGLang | `p6-b300.48xlarge` | ⏳ [待补充](results/minimax-m3.1-flash_p6-b300.md) |
| P2 | Mistral-Large-4-1T-A52B | vLLM + SGLang | `p6-b300.48xlarge` | ⏳ [待补充](results/mistral-large-4_p6-b300.md) |
| P2 | Qwen3.8-2.4T-A95B（NVFP4） | SGLang | `p6-b300.48xlarge` | ⏳ [待补充](results/qwen3.8-2.4t-a95b_p6-b300.md) |

### 如何补充你的结果

1. 打开该行的占位文档（`docs/results/<model>_<instance>.md`，模板 [`results/TEMPLATE.md`](results/TEMPLATE.md)），按其中的启动命令起服务（有改动写明）。
2. 在同一台实例上跑文档里的两条 `bench/llm_bench.py` 命令（W1 1024/256、W2 8192/1024，并发 1/8/32/64），`--out` 指向 `results/<model>_<instance>/<框架>_w1_1024_256` 等，生成 `.json` + `.md`。
3. 把 JSON/MD 提交到 `results/<model>_<instance>/`，把数字填进占位文档的结果表，补齐版本、日期、运行者、实际成本，并把状态行改为 ✅。
4. 把本表（[README](../README.md#-实测结果) 与本文件各一份）对应行改为 `✅ 已实测`，走 feature 分支 + PR。
5. 跑完立刻终止实例：`python scripts/teardown.py --name <Name tag>`，再用 `aws ec2 describe-instances` 确认 `terminated`。

## 测试方法（所有 OpenAI 兼容框架统一）

- 工具：[`bench/llm_bench.py`](../bench/llm_bench.py)，客户端与服务端在同一台实例上，走 `127.0.0.1`，排除网络影响。
- 两组定长负载，每组跑并发 1 / 8 / 32 / 64：
  - **W1 对话**：输入 1024 token，输出 256 token；
  - **W2 长输入**：输入 8192 token，输出 1024 token（与 SGLang cookbook 的 8K/1K 口径一致，方便与 [`PERF_PUBLISHED.md`](PERF_PUBLISHED.md) 对照）。
- 每个并发级别的请求数 = 4 × 并发（至少 16），另加 2 个不计时的预热请求；`ignore_eos` + `min_tokens` 固定输出长度；`temperature=0`。
- 指标：TTFT、TPOT、ITL（p50/p90/p99）、输出 tok/s、请求/s；结果写 `results/<model>_<framework>_<instance>.{json,md}`。
- 启动命令严格用 [`practice/`](practice/) 中的官方命令，不调参；同一模型的 vLLM 与 SGLang 在**同一台实例上先后跑**，节省一次下载与开机。
- DeepInfer 没有 HTTP 服务，改用它自带的 `examples/benchmark.py`（见 [`practice/deepinfer.md`](practice/deepinfer.md)），结果单独成表，不与在线压测混比。
- 每次跑完立即终止实例；权重下载到实例 NVMe，不长期保留 EBS。

## 运行清单与成本

时长 = 开机 + 拉镜像 + 下载/加载权重 + 每个框架 2 组负载 × 4 个并发级别 + 余量。下载按约 1 GB/s 估计（1 TB 级权重约 20–30 分钟），每个框架的压测约 1–1.5 小时。

| 优先级 | 模型 | 框架 | 实例 | 预估小时 | 单价 | 预估成本 |
|---|---|---|---|---:|---:|---:|
| P0 | gpt-oss-120b | vLLM + SGLang（同一台） | `p5.48xlarge` ×1 | 3 | $55.04/h | $165.12 |
| P0 | Qwen3.8-27B-FP8 | vLLM + SGLang（同一台；**非官方硬件**；✅ 已实测，ap-northeast-1 / g6e.xlarge，见 [结果](results/qwen3.8-27b_g6e.md)） | `g6e.xlarge` ×1（1×L40S 48GB） | 3 | $1.861/h | $5.58 |
| P0 | Qwen3-Omni-30B-A3B-Instruct | vLLM-Omni（默认 2 卡配置，文本输出） | `p5.48xlarge` ×1 | 2 | $55.04/h | $110.08 |
| P0 | GLM-5.3-Flash | vLLM + SGLang（同一台，H100 配置均为 verified） | `p5.48xlarge` ×1 | 4 | $55.04/h | $220.16 |
| P0 | GLM-5.3-Flash | TrnRT：构建编译缓存（CPU，「数小时」） | `m7i.16xlarge` ×1 | 8 | $3.2256/h | $25.80 |
| P0 | GLM-5.3-Flash | TrnRT：服务 + 压测 | `trn2.48xlarge` ×1，8 小时 Capacity Block | 8（整块计费） | $35.76/h | $289.66 |
| P0 | DeepSeek-V4.1-Flash-1017 | vLLM + SGLang（同一台） | `p5en.48xlarge` ×1 | 4 | $63.296/h | $253.18 |
| P1 | DeepSeek-V4.1-Flash-1017 | DeepInfer（离线 `benchmark.py`，EP8；含源码构建） | `p6-b200.48xlarge` ×1 | 4 | $113.9328/h | $455.73 |
| P1 | GLM-5.3 | vLLM + SGLang（同一台，H200 均为 verified） | `p5en.48xlarge` ×1 | 4 | $63.296/h | $253.18 |
| P1 | DeepSeek-V4-Pro-0813 | vLLM + SGLang（同一台） | `p5en.48xlarge` ×1 | 5 | $63.296/h | $316.48 |
| P1 | MiniMax-M3.1-Flash | SGLang（H200 verified；vLLM 只有 B300 配置，见 P2） | `p5en.48xlarge` ×1 | 3 | $63.296/h | $189.89 |
| P2 | MiniMax-M3.1-Flash + Mistral-Large-4 | vLLM + SGLang（同一台依次跑，B300 配置） | `p6-b300.48xlarge` ×1 | 6 | $142.416/h | $854.50 |
| P2 | Qwen3.8-2.4T-A95B（NVFP4） | SGLang（单机 NVFP4，cookbook verified） | `p6-b300.48xlarge` ×1 | 4 | $142.416/h | $569.66 |

| 合计 | 成本 |
|---|---:|
| P0 | $1,069.59 |
| P1 | $1,215.28 |
| P2 | $1,424.16 |
| **全部** | **$3,709.03** |

未计入：EBS / 数据传输（权重放实例 NVMe，结果只有 KB 级）、失败重跑、Capacity Block 之外排队等待。建议先审批 P0，跑通流程后再决定 P1/P2。

### 不在本期计划内

| 组合 | 原因 |
|---|---|
| Kimi-K3.1-Pro（任何框架） | vLLM recipe 只有 GB300 / VR200 / TPU 配置，SGLang 的 B300 配置标为 in-progress；AWS 上对应 `p6e-gb300` UltraServer，规模与成本远超本仓库目标 |
| Qwen3.8-2.4T-A95B × vLLM | recipe 需要 2×B300 多机（TP16），2 × $142.416/h，留待单机结果出来后再定 |
| DeepInfer 生产规模 | 最小高效单元 128 张 GPU（64P + 64D），且 PD 分离与 KV cache 组件未开源 |

## 风险与前提

- **容量**：p5 / p5en / p6 按需实例常常没有现货，可能要用 [Capacity Blocks](https://aws.amazon.com/ec2/capacityblocks/) 或换区，价格会变化。trn2.48xlarge 在美国区只能通过 Capacity Block 获取。
- **配额**：账户需要对应实例族的 vCPU 配额（例如一台 `p5.48xlarge` 就要 192 vCPU）。
- **非官方组合**：g6e 上的 Qwen3.8-27B-FP8 没有官方 recipe，结果只作参考；若显存或算子不支持，记录失败原因即可，不追加时长。
- **许可证**：MiniMax-M3.1-Flash 默认只授权非商业用途，内部评测属于非商业使用；其他模型见 [`SUPPORT_MATRIX.md`](SUPPORT_MATRIX.md#-许可证要点转述以原文为准)。

## 价格来源

| 实例 | 单价 | 来源 |
|---|---|---|
| `p5.48xlarge` | $55.04/h | AWS Price List API（`aws pricing get-products`，Linux、共享租户、按需，us-east-1 / us-east-2 / us-west-2 同价，生效日期 2026-11-01） |
| `p5en.48xlarge`（`p5e.48xlarge` 同价，us-east-1 无 p5e） | $63.296/h | 同上 |
| `p6-b200.48xlarge` | $113.9328/h | 同上 |
| `p6-b300.48xlarge` | $142.416/h | 同上（us-east-1、us-west-2；us-east-2 无报价） |
| `g6e.xlarge` / `g6e.12xlarge` | $1.861/h / $10.49264/h | 同上 |
| `m7i.16xlarge` | $3.2256/h | 同上（us-east-2） |
| `trn2.48xlarge` | $35.76/h（Capacity Block） | `aws ec2 describe-capacity-block-offerings`，us-east-2b，2026-11-27：24 小时块 $858.26、8 小时块 $289.66（均折合 $35.76/h）；与 [TrnRT README](https://github.com/RunanywhereAI/trnrt#where-trnrt-stands) 引用的 2026-11-24 Capacity Block 价格一致。Price List 中美国区无 trn2 按需价 |

公开价格页：[EC2 按需价格](https://aws.amazon.com/ec2/pricing/on-demand/)、[Capacity Blocks 价格](https://aws.amazon.com/ec2/capacityblocks/pricing/)。
