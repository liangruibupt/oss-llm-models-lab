# DeepSeek-V4.1-Flash-1017 · p6-b200.48xlarge（实测结果）

> 状态：⏳ 待补充 · 对应 [`../BENCH_PLAN.md`](../BENCH_PLAN.md) 中的一行。跑完后把本页的「待补充」全部替换掉，并把 README 与 BENCH_PLAN 的「📊 实测结果」表里这一行改成 ✅。

| 项 | 值 |
|---|---|
| 模型 | [deepseek-ai/DeepSeek-V4.1-Flash-1017](https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash-1017) |
| 框架 | DeepInfer |
| 实例 | `p6-b200.48xlarge` |
| 精度 | 原生 FP4/FP8 混合 |
| 预估成本（BENCH_PLAN） | 4 h · $455.73 |
| 实际实例小时 / 成本 | 待补充 |
| 运行日期（UTC） | 待补充 |
| 运行者 | 待补充 |
| 原始数据目录 | [`results/deepseek-v4.1-flash_p6-b200_deepinfer/`](../../results/deepseek-v4.1-flash_p6-b200_deepinfer/) |

## 版本

| 项 | 值 |
|---|---|
| AMI / 驱动 / CUDA | 待补充 |
| 框架版本与镜像 digest | 待补充 |
| torch / CUDA（容器内） | 待补充 |
| 权重 repo 与 revision | 待补充 |
| 峰值显存 | 待补充 |

## 启动命令（来自 [`../practice/`](../practice/)，有改动请写明）

**DeepInfer 离线基准**（来源 [`../practice/deepinfer.md`](../practice/deepinfer.md)）

```bash
export WORLD_SIZE=1 RANK=0
export CUDA_VISIBLE_DEVICES=0,1,2,3,4,5,6,7
python examples/benchmark.py --result_jsonl results/deepinfer_v41flash_p6b200.jsonl
# CP8 + 更大的 prefill chunk（README 示例）
python examples/benchmark.py --cp 8 --prefill_batch_size 65536
# 关闭投机解码做对照
DEEPINFER_USE_NEXTN_DECODE=0 python examples/benchmark.py
```

## 压测命令

见上方 DeepInfer 离线基准命令，加 `--result_jsonl results/deepseek-v4.1-flash_p6-b200_deepinfer/deepinfer.jsonl`。

## 结果

DeepInfer 没有 HTTP 服务，`bench/llm_bench.py` 不适用；用 `examples/benchmark.py` 的三项指标：

| 配置 | prefill 吞吐 (tok/s/GPU) | decode avg_SPS | decode 吞吐 (tok/s/GPU，全接受口径) |
|---|---:|---:|---:|
| 默认（EP8，nextn=5） | 待补充 | 待补充 | 待补充 |
| `DEEPINFER_USE_NEXTN_DECODE=0` | 待补充 | 待补充 | 待补充 |


## 结论

待补充
