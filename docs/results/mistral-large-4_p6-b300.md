# Mistral-Large-4-1T-A52B · p6-b300.48xlarge（实测结果）

> 状态：⏳ 待补充 · 对应 [`../BENCH_PLAN.md`](../BENCH_PLAN.md) 中的一行。跑完后把本页的「待补充」全部替换掉，并把 README 与 BENCH_PLAN 的「📊 实测结果」表里这一行改成 ✅。

| 项 | 值 |
|---|---|
| 模型 | [mistralai/Mistral-Large-4-1T-A52B](https://huggingface.co/mistralai/Mistral-Large-4-1T-A52B) |
| 框架 | vLLM + SGLang |
| 实例 | `p6-b300.48xlarge` |
| 精度 | vLLM 用 NVFP4 checkpoint，SGLang 用 FP8 |
| 预估成本（BENCH_PLAN） | 与 MiniMax-M3.1-Flash 同机，合计 6 h · $854.50 |
| 实际实例小时 / 成本 | 待补充 |
| 运行日期（UTC） | 待补充 |
| 运行者 | 待补充 |
| 原始数据目录 | [`results/mistral-large-4_p6-b300/`](../../results/mistral-large-4_p6-b300/) |

## 版本

| 项 | 值 |
|---|---|
| AMI / 驱动 / CUDA | 待补充 |
| 框架版本与镜像 digest | 待补充 |
| torch / CUDA（容器内） | 待补充 |
| 权重 repo 与 revision | 待补充 |
| 峰值显存 | 待补充 |

## 启动命令（来自 [`../practice/`](../practice/)，有改动请写明）

**vLLM**（来源 [`../practice/vllm.md`](../practice/vllm.md)）

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

**SGLang**（来源 [`../practice/sglang.md`](../practice/sglang.md)）

**p6-b300.48xlarge（8×B300） · 策略 `high-throughput` · cookbook 状态：verified** · [cookbook 原始配置](https://docs.sglang.io/cookbook/autoregressive/Mistral/Mistral-Large-4#hw=b300&variant=default&quant=fp8&strategy=high-throughput&nodes=single)

```bash
sglang serve \
  --model-path mistralai/Mistral-Large-4-1T-A52B \
  --tp-size 8 \
  --mem-fraction-static 0.85 \
  --reasoning-parser auto \
  --tool-call-parser auto \
  --host 0.0.0.0 \
  --port 30000
```

## 压测命令

客户端与服务端在同一台实例上。`<PORT>`：vLLM 8000，SGLang 30000，TrnRT 8000，vLLM-Omni 8091。

```bash
# W1 对话：1024 输入 / 256 输出
python3 bench/llm_bench.py --base-url http://127.0.0.1:<PORT>/v1 --model mistralai/Mistral-Large-4-1T-A52B \
  --input-len 1024 --output-len 256 --concurrency 1,8,32,64 \
  --label "<框架 版本> / p6-b300.48xlarge / vLLM 用 NVFP4 checkpoint，SGLang 用 FP8 / W1" --out results/mistral-large-4_p6-b300/<框架>_w1_1024_256
# W2 长输入：8192 输入 / 1024 输出
python3 bench/llm_bench.py --base-url http://127.0.0.1:<PORT>/v1 --model mistralai/Mistral-Large-4-1T-A52B \
  --input-len 8192 --output-len 1024 --concurrency 1,8,32,64 \
  --label "<框架 版本> / p6-b300.48xlarge / vLLM 用 NVFP4 checkpoint，SGLang 用 FP8 / W2" --out results/mistral-large-4_p6-b300/<框架>_w2_8192_1024
```

## 结果

### vLLM

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

### SGLang

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
