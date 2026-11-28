# 🖥 DeepSeek-V4.1-Flash 在 H20 / RTX PRO 6000D 上能跑吗？

> **checked 2026-11-28**。本页只整理公开资料，**本仓库未实测**。每个数字都标注来源类型（官方 = 框架或模型方发布；第三方 = 社区或其他机构），不同来源的负载和口径不同，**不能跨表直接比较**。

## 一句话结论

| GPU | 能否跑起来 | 公开 benchmark | 说明 |
|---|---|---|---|
| **H20（96 GB HBM3，SM90 Hopper）** | 🟡 **按显存推算可以（8 卡 TP8），未找到公开实测** | ❌ 未找到 | 8×96 GB = 768 GB，高于 vLLM recipe 给出的最低 614 GB；H20 与 H100/H200 同为 SM90，但 vLLM recipe 的硬件列表里没有 H20 |
| **H20-3e（HBM3e 版，141 GB）** | ✅ **已有公开实测**（SGLang，单机 8 卡） | ✅ 第三方：LMSYS 博客（SGLang 实验分支） | 4P+4D 机内 PD 分离，输出约 2,465 tok/s |
| **RTX PRO 6000D（85 GB，SM120 Blackwell）** | ✅ **已有公开实测**（vLLM nightly + 两个 SM120 补丁，单机 8 卡 TP8） | ✅ 第三方：力数智能（lexdata）开源仓库 | 并发 32 时 1,046–1,284 tok/s；无 NVLink，需 `NCCL_P2P_LEVEL=SYS` |
| RTX PRO 6000（96 GB，非 D 版，SM120） | ✅ 社区多个方案（2/4/8 卡） | ✅ 第三方：见第 4 节 | 作为 6000D 的参照 |

## 1. 先算显存：模型有多大

来自 [vLLM 官方 recipe](https://recipes.vllm.ai/deepseek-ai/DeepSeek-V4.1-Flash) 的 Memory 一节（官方）：

| 组成 | 存储大小 |
|---|---:|
| 路由专家 + DSpark 专家（MXFP4） | 259.5 GiB |
| Engram 表（FP8） | 183.1 GiB |
| Attention / dense / router（FP8） | 6.9 GiB |
| Embedding + LM head（BF16）、norm（FP32） | 3.9 GiB |
| UE8M0 block scale | 21.9 GiB |
| **合计** | **约 476 GiB（511 GB）** |

- recipe 的 `vram_minimum_gb` 为 **614 GB**（总量 × 1.2 余量）。
- **Engram CPU offload**（`--engram-config '{"cpu_offload":true}'`）可以把 Engram 表放到主机 pinned 内存，通过 UVA 读取，输出不变。H200 TP4 就靠它每卡省下 23.6 GiB。
- KV cache 很小：DeepSeek 公布全局 KV 为 **890 字节/token**（[技术报告](https://arxiv.org/pdf/2609.19969)），1M 上下文不到 1 GB 全局 KV。容量上限主要由权重决定。
- vLLM recipe 列出的硬件：`h100`、`h200`、`b200`、`gb200`、`b300`、`gb300`、`dgx_station_gb300`、MI300X/325X/350X/355X、Ascend 950DT/910B。**没有 H20，也没有 SM120（RTX PRO 6000 系列）**。

## 2. H20 / H20-3e

### 2.1 H20（96 GB）：可行性推算，未找到实测

- **8 卡**：768 GB ≥ 614 GB，TP8 放得下，并给 KV 留出约 150 GB 余量。同为 SM90 的 8×H100（640 GB）在 vLLM recipe 的硬件列表里。
- **4 卡**：384 GB < 476 GiB，即使把 Engram 表（183.1 GiB）卸到主机内存，剩余约 293 GiB 权重也只剩很少的 KV 空间，不建议。
- **2026-11-28 未找到 96 GB H20 的公开 benchmark**。下面 2.2 的 LMSYS 数据用的是 H20-3e。如果要在 96 GB H20 上复现，先按 8 卡 TP8 部署，再参考 2.2 的 SGLang 配置。

### 2.2 H20-3e：SGLang 单机 8 卡（第三方 · LMSYS / SGLang 团队）

来源：[Optimizing DeepSeek-V4.1-Flash PD & Colocate Serving on H20-3e](https://www.lmsys.org/blog/2026-11-19-deepseek-v41-h20)（2026-11-19）。

**负载**：256 个请求，并发 24；每个请求 61,440 共享前缀 token + 4,096 独有 token，输出 500 token；实测前缀缓存命中率 93.21%。Humming W4A8 MoE，DSpark block size 5，8,192 token prefill chunk。

**PD 分离（GPU 0–3 prefill，GPU 4–7 decode，Mooncake NVLink 传 KV）**：

| 配置 | 平均 E2E (ms) | 输出 tok/s | 平均 TTFT (ms) | 平均 TPOT (ms) |
|---|---:|---:|---:|---:|
| TP4 基线 | 13,633.80 | 846.76 | 12,037.73 | 3.20 |
| 最终配置（prefill CP + decode DP + FP8 DeepGEMM + breakable CUDA graph + TP MoE 等 7 步） | **4,698.65** | **2,464.90** | 1,894.54 | 5.62 |

**并发扫描（同一负载）**：

| 并发 | TP4 E2E (ms) | 最终 E2E (ms) | TP4 输出 tok/s | 最终输出 tok/s |
|---:|---:|---:|---:|---:|
| 8 | 4,798.86 | 2,690.09 | 826.73 | 1,462.65 |
| 16 | 9,178.42 | 3,678.99 | 854.19 | 2,121.03 |
| 24 | 13,563.03 | 4,698.65 | 853.98 | 2,464.90 |
| 32 | 17,843.62 | 6,097.87 | 852.97 | 2,502.19 |

**单个 4 卡 worker 混合部署（colocate，并发 24）**：输出吞吐 642.46 → **1,482.72 tok/s**，平均 E2E 18.62 s → 7.96 s。按每 GPU 计，colocate 为 371 tok/s，PD 为 308 tok/s；PD 的延迟更低、总吞吐更高。

**精度**：GSM8K 基线 96.50%，最终 96.42%。

**注意**：

- 复现要用实验分支 `SYChen123/sglang:v4.1/h20-dev-pd-blog` 的 commit `b07c70112c175eb7ca3c157c7bbc7847cc398d7d`。第 2、5–7 步和 colocate decode DP 在博客发布时还在上游 review 中，**不在 SGLang 正式版里**。
- Hopper 上 FP8 DeepGEMM 打分需设 `SGLANG_DSV41_TORCH_PREFILL_INDEXER=0` 和 `SGLANG_DSV41_SM90_PREFILL_INDEXER=deepgemm`。
- 该环境不支持 DeepEP / MegaMoE all-to-all，所以对比的是 `--moe-a2a-backend none` 下的 EP 与 TP MoE。

完整启动命令（prefill / decode / router / colocate）和 `sglang.bench_serving` 命令见原文 Reproduction 一节。

## 3. RTX PRO 6000D：vLLM 单机 8 卡 TP8（第三方 · 力数智能 lexdata）

来源：[luqidaxia/deepseekv41_pro6000d_tp8](https://github.com/luqidaxia/deepseekv41_pro6000d_tp8)（MIT，含部署脚本、补丁、原始 JSON）。

**硬件**：XFUSION x86 单机，8× RTX 6000D（SM120，每卡 85 GB，合计约 669 GiB），128 核 CPU，755 GB 内存，驱动 595.91.07。**无 NVLink**，4 颗 PCIe Gen5 交换芯片，每 2 卡一颗。

**软件**：`vllm/vllm-openai:nightly`（build `81198e97`）+ 两个 SM120 分发表补丁（indexer block 64、extra page 32），否则在 SM120 上会失败。

**负载**：TP8，512K 上下文，贪心解码，`max_tokens=512`，每个请求带唯一 nonce（前缀缓存命中 0%），DSpark 6 个 draft。

| 场景 | 并发 | 输出 tok/s（seqs=6 / cg=48） | 输出 tok/s（seqs=32 / cg=224，调优后） | TTFT（调优后） |
|---|---:|---:|---:|---:|
| 散文 | 1 | 155.5 | 153.5 | 56 ms |
| 散文 | 16 | 466.4 | 817.6 | 245 ms |
| 散文 | 32 | 467.4 | **1,045.6** | 450 ms |
| 代码 | 1 | 227.8 | 210.1 | 60 ms |
| 代码 | 16 | 568.6 | 993.7 | 246 ms |
| 代码 | 32 | 608.6 | **1,283.5** | 459 ms |

**显存与 KV**：每卡常驻权重约 59 GiB / 85.6 GiB，KV cache 23 GiB/卡，KV 池 9,097,928 token；512K 上下文约 17 路、1M 上下文约 8 路可同时跑满。DSpark 接受长度 3.1–3.5。

**关键经验**：

- **`NCCL_P2P_LEVEL=SYS`**：默认只有同交换芯片的 4 跳走 P2P，另一半 ring 退回共享内存。设为 SYS 后 1 MB all-reduce busBW 从 10.63 提到 15.23 GB/s（+43%，微基准；端到端收益作者未可靠测量）。vLLM 自带的 custom all-reduce 在超过 2 张纯 PCIe 卡时自动禁用。
- **`--max-cudagraph-capture-size = ceil8(max_num_seqs × (num_speculative_tokens + 1))`**：两者不联动时，超出的并发退回 eager。作者实测并发 7 比并发 6 慢 56%。
- KV 预留 23 GiB 是验证过的上限，24 GiB 能启动但负载下 OOM。
- `--default-chat-template-kwargs '{"thinking": false}'` 让思考按需开启，否则每个请求都会思考。

关键参数（摘自原仓库）：

```bash
-e NCCL_P2P_LEVEL=SYS
--tensor-parallel-size 8 --kv-cache-dtype fp8 --block-size 64
--max-model-len 512000 --max-num-seqs 32 --max-num-batched-tokens 8192
--max-cudagraph-capture-size 224 --gpu-memory-utilization 0.85
--kv-cache-memory-bytes 24696061952
--enable-prefix-caching --enable-chunked-prefill
--reasoning-parser deepseek_v41 --tool-call-parser deepseek_v41 --enable-auto-tool-choice
--default-chat-template-kwargs '{"thinking": false}'
--speculative-config '{"method": "dspark", "num_speculative_tokens": 6, "draft_sample_method": "probabilistic"}'
```

## 4. 参照：RTX PRO 6000（96 GB，非 D 版）社区方案

| 方案 | 卡数 | 要点 | 来源 |
|---|---:|---|---|
| SGLang issue #40877 现场报告（第三方，实际用的是 vLLM 镜像） | 8× Max-Q | TP8，1M 上下文，FP8 KV，DSpark 5；KV 池 2,983,601 token。约 200K 输入、并发 8：每请求 decode 5.7 tok/s，TTFT 中位数 61.59 s | [sgl-project/sglang#40877](https://github.com/sgl-project/sglang/issues/40877) |
| vLLM 8 卡踩坑清单（第三方） | 8 | 1M 上下文已验证；每卡约 91 GB / 96 GB，Engram 表占大头 | [vllm-project/vllm#56700](https://github.com/vllm-project/vllm/issues/56700) |
| 4 卡 + NVMe Engram（第三方） | 4 | TP4，FP8 KV，Engram 查表放 NVMe，1M 上下文 | [samuelcardillo/deepseek-v41-flash-1017-4x-rtx-pro-6000](https://github.com/samuelcardillo/deepseek-v41-flash-1017-4x-rtx-pro-6000) |
| 4 卡 + DDR5 缓存 Engram（第三方） | 4 | Engram 行放有界 DDR5 缓存，未命中读 NVMe | [sybil-solutions/deepseek-v4.1-flash-4x-rtx-pro-6000](https://github.com/sybil-solutions/deepseek-v4.1-flash-4x-rtx-pro-6000) |
| vLLM-Moet SM120 文档（第三方） | 4 | TP4，512K 上下文，DSpark k=7，KV 卸载到内存和磁盘 | [kacper-daftcode/vLLM-Moet](https://github.com/kacper-daftcode/vLLM-Moet/blob/main/docs/dsv41-sm120.md) |
| 2 卡 3-bit EXL3（第三方） | 2 | 量化版，部分专家、Engram 和 embedding 放主机内存 | [HF 模型卡](https://huggingface.co/Nateemerson/DeepSeek-V4.1-Flash-1017-EXL3-3bpw-2x-RTX-PRO-6000) |

4 卡及以下的方案都要把 Engram 或部分专家卸到主机内存或 NVMe，速度和上下文都会受影响。表中只有 #40877 的数字经过本页核对，其余仅列要点。

## 5. 与本仓库 AWS 机型的对应

- AWS 上没有 H20 或 RTX PRO 6000D（两者是面向中国市场的型号）。
- 同为 SM120 的 RTX PRO 6000 Blackwell 在 AWS 对应 **g7e** 系列：`aws ec2 describe-instance-types` 显示 GPU 为 "RTX PRO Server 6000"，每卡 98,304 MiB（96 GB），g7e.48xlarge 为 8 卡（2026-11-28 查询）。可以参考第 3、4 节的 SM120 补丁和 NCCL 设置；本仓库尚未在 g7e 上实测 DeepSeek-V4.1-Flash。
- 同为 SM90 的 Hopper 在 AWS 对应 p5（H100）/ p5en（H200），见 [`BENCH_PLAN.md`](../BENCH_PLAN.md) 和 [`practice/vllm.md`](../practice/vllm.md)。

## 来源

- vLLM：[DeepSeek-V4.1-Flash recipe](https://recipes.vllm.ai/deepseek-ai/DeepSeek-V4.1-Flash)（官方）
- DeepSeek：[DeepSeek-V4.1-Flash 技术报告（KV cache 压缩）](https://arxiv.org/pdf/2609.19969)（官方）
- LMSYS：[DeepSeek-V4.1-Flash PD & Colocate Serving on H20-3e](https://www.lmsys.org/blog/2026-11-19-deepseek-v41-h20)（第三方，SGLang 团队）
- 力数智能：[luqidaxia/deepseekv41_pro6000d_tp8](https://github.com/luqidaxia/deepseekv41_pro6000d_tp8)（第三方）
- 第 4 节各社区仓库与 issue（第三方）

（以上内容为转述整理，非原文引用。）
