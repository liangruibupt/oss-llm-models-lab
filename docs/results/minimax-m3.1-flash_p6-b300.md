# MiniMax-M3.1-Flash · p6-b300.48xlarge（实测结果）

> 状态：⏳ 待补充 · 对应 [`../BENCH_PLAN.md`](../BENCH_PLAN.md) 中的一行。跑完后把本页的「待补充」全部替换掉，并把 README 与 BENCH_PLAN 的「📊 实测结果」表里这一行改成 ✅。

| 项 | 值 |
|---|---|
| 模型 | [MiniMaxAI/MiniMax-M3.1-Flash](https://huggingface.co/MiniMaxAI/MiniMax-M3.1-Flash) |
| 框架 | vLLM + SGLang |
| 实例 | `p6-b300.48xlarge` |
| 精度 | 原生权重 |
| 预估成本（BENCH_PLAN） | 与 Mistral-Large-4 同机，合计 6 h · $854.50 |
| 实际实例小时 / 成本 | 待补充 |
| 运行日期（UTC） | 待补充 |
| 运行者 | 待补充 |
| 原始数据目录 | [`results/minimax-m3.1-flash_p6-b300/`](../../results/minimax-m3.1-flash_p6-b300/) |

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

**p6-b300.48xlarge（8×B300） · single_node_tp · 1 节点 · recipe 状态：verified · 镜像 `vllm/vllm-openai:minimax-m31-flash`**

```bash
export VLLM_FLOAT32_MATMUL_PRECISION=high
vllm serve MiniMaxAI/MiniMax-M3.1-Flash \
  --block-size 128 \
  --disable-hybrid-kv-cache-manager \
  --tensor-parallel-size 8 \
  --kv-cache-dtype nvfp4 \
  --attention-config '{"indexer_kv_dtype": "nvfp4", "use_prefill_query_quantization": true}' \
  --compilation-config '{"cudagraph_mode": "FULL_AND_PIECEWISE"}' \
  --tool-call-parser minimax_m3 \
  --enable-auto-tool-choice \
  --reasoning-parser minimax_m3 \
  --speculative-config '{"method":"dspark","num_speculative_tokens":7,"attention_backend":"FLASHINFER_TS","kv_cache_dtype":"fp8","draft_sample_method":"probabilistic","rejection_sample_method":"block"}'
```

**SGLang**（来源 [`../practice/sglang.md`](../practice/sglang.md)）

**p6-b300.48xlarge（8×B300） · 策略 `balanced` · cookbook 状态：verified** · [cookbook 原始配置](https://docs.sglang.io/cookbook/autoregressive/MiniMax/MiniMax-M3.1#hw=b300&variant=flash&quant=nvfp4&strategy=balanced&nodes=single&spec=dspark)

```bash
export FMHA_SM100_ALLOW_JIT=1
FMHA_SM100_ALLOW_JIT=1 \
sglang serve \
  --trust-remote-code \
  --model-path MiniMaxAI/MiniMax-M3.1-Flash \
  --reasoning-parser minimax-m3 \
  --tool-call-parser minimax-m3 \
  --tp 4 \
  --moe-runner-backend flashinfer_trtllm_routed \
  --speculative-algorithm DSPARK \
  --speculative-use-block-verification \
  --cuda-graph-backend-prefill breakable \
  --chunked-prefill-size 32768 \
  --max-running-requests 128 \
  --cuda-graph-max-bs-decode 128 \
  --mem-fraction-static 0.8 \
  --tokenizer-worker-num 8 \
  --host 0.0.0.0 \
  --port 30000
```

## 压测命令

客户端与服务端在同一台实例上。`<PORT>`：vLLM 8000，SGLang 30000，TrnRT 8000，vLLM-Omni 8091。

```bash
# W1 对话：1024 输入 / 256 输出
python3 bench/llm_bench.py --base-url http://127.0.0.1:<PORT>/v1 --model MiniMaxAI/MiniMax-M3.1-Flash \
  --input-len 1024 --output-len 256 --concurrency 1,8,32,64 \
  --label "<框架 版本> / p6-b300.48xlarge / 原生权重 / W1" --out results/minimax-m3.1-flash_p6-b300/<框架>_w1_1024_256
# W2 长输入：8192 输入 / 1024 输出
python3 bench/llm_bench.py --base-url http://127.0.0.1:<PORT>/v1 --model MiniMaxAI/MiniMax-M3.1-Flash \
  --input-len 8192 --output-len 1024 --concurrency 1,8,32,64 \
  --label "<框架 版本> / p6-b300.48xlarge / 原生权重 / W2" --out results/minimax-m3.1-flash_p6-b300/<框架>_w2_8192_1024
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
