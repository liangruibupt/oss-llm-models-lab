# Qwen3-Omni-30B-A3B-Instruct · p5.48xlarge（实测结果）

> 状态：⏳ 待补充 · 对应 [`../BENCH_PLAN.md`](../BENCH_PLAN.md) 中的一行。跑完后把本页的「待补充」全部替换掉，并把 README 与 BENCH_PLAN 的「📊 实测结果」表里这一行改成 ✅。

| 项 | 值 |
|---|---|
| 模型 | [Qwen/Qwen3-Omni-30B-A3B-Instruct](https://huggingface.co/Qwen/Qwen3-Omni-30B-A3B-Instruct) |
| 框架 | vLLM-Omni（文本输出） |
| 实例 | `p5.48xlarge` |
| 精度 | BF16 |
| 预估成本（BENCH_PLAN） | 2 h · $110.08 |
| 实际实例小时 / 成本 | 待补充 |
| 运行日期（UTC） | 待补充 |
| 运行者 | 待补充 |
| 原始数据目录 | [`results/qwen3-omni-30b-a3b_p5/`](../../results/qwen3-omni-30b-a3b_p5/) |

## 版本

| 项 | 值 |
|---|---|
| AMI / 驱动 / CUDA | 待补充 |
| 框架版本与镜像 digest | 待补充 |
| torch / CUDA（容器内） | 待补充 |
| 权重 repo 与 revision | 待补充 |
| 峰值显存 | 待补充 |

## 启动命令（来自 [`../practice/`](../practice/)，有改动请写明）

**vLLM-Omni**（来源 [`../practice/vllm-omni.md`](../practice/vllm-omni.md)）

```bash
vllm serve Qwen/Qwen3-Omni-30B-A3B-Instruct --omni --port 8091
```

压测时加 `--extra-body '{"modalities": ["text"]}'`，端口 8091。

## 压测命令

客户端与服务端在同一台实例上。`<PORT>`：vLLM 8000，SGLang 30000，TrnRT 8000，vLLM-Omni 8091。

```bash
# W1 对话：1024 输入 / 256 输出
python3 bench/llm_bench.py --base-url http://127.0.0.1:<PORT>/v1 --model Qwen/Qwen3-Omni-30B-A3B-Instruct \
  --input-len 1024 --output-len 256 --concurrency 1,8,32,64 \
  --label "<框架 版本> / p5.48xlarge / BF16 / W1" --out results/qwen3-omni-30b-a3b_p5/<框架>_w1_1024_256
# W2 长输入：8192 输入 / 1024 输出
python3 bench/llm_bench.py --base-url http://127.0.0.1:<PORT>/v1 --model Qwen/Qwen3-Omni-30B-A3B-Instruct \
  --input-len 8192 --output-len 1024 --concurrency 1,8,32,64 \
  --label "<框架 版本> / p5.48xlarge / BF16 / W2" --out results/qwen3-omni-30b-a3b_p5/<框架>_w2_8192_1024
```

## 结果

### vLLM-Omni（文本输出）

| 负载 | 并发 | TTFT p50 (ms) | TTFT p99 (ms) | TPOT p50 (ms) | TPOT p99 (ms) | 输出 tok/s | 请求/s |
|---|---:|---:|---:|---:|---:|---:|---:|
| W1 1024/256 | 1 | 待补充 | 待补充 | 待补充 | 待补充 | 待补充 | 待补充 |
| W1 1024/256 | 8 | 待补充 | 待补充 | 待补充 | 待补充 | 待补充 | 待补充 |
| W1 1024/256 | 32 | 待补充 | 待补充 | 待补充 | 待补充 | 待补充 | 待补充 |
| W1 1024/256 | 64 | 待补充 | 待补充 | 待补充 | 待补充 | 待补充 | 待补充 |
| W2 8192/1024 | 1 | 待补充 | 待补充 | 待补充 | 待补充 | 待补充 | 待补充 |
| W2 8192/1024 | 8 | 待补充 | 待补充 | 待补充 | 待补充 | 待补充 | 待补充 |
| W2 8192/1024 | 32 | 待补充 | 待补充 | 待补充 | 待补充 | 待补充 | 待补充 |
| W2 8192/1024 | 64 | 待补充 | 待补充 | 待补充 | 待补充 | 待补充 | 待补充 |


## 结论

待补充
