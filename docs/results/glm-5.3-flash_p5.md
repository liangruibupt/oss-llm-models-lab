# GLM-5.3-Flash · p5.48xlarge（实测结果）

> 状态：⏳ 待补充 · 对应 [`../BENCH_PLAN.md`](../BENCH_PLAN.md) 中的一行。跑完后把本页的「待补充」全部替换掉，并把 README 与 BENCH_PLAN 的「📊 实测结果」表里这一行改成 ✅。

| 项 | 值 |
|---|---|
| 模型 | [zai-org/GLM-5.3-Flash](https://huggingface.co/zai-org/GLM-5.3-Flash) |
| 框架 | vLLM + SGLang |
| 实例 | `p5.48xlarge` |
| 精度 | FP8（原生权重） |
| 预估成本（BENCH_PLAN） | 4 h · $220.16 |
| 实际实例小时 / 成本 | 待补充 |
| 运行日期（UTC） | 待补充 |
| 运行者 | 待补充 |
| 原始数据目录 | [`results/glm-5.3-flash_p5/`](../../results/glm-5.3-flash_p5/) |

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

**p5.48xlarge（8×H100 80GB） · single_node_tp · 1 节点 · recipe 状态：verified · 镜像 `vllm/vllm-openai:nightly`**

```bash
export VLLM_ENGINE_READY_TIMEOUT_S=3600 VLLM_USE_RUST_FRONTEND=1
vllm serve zai-org/GLM-5.3-Flash \
  --tokenizer-mode glm5_next \
  --tensor-parallel-size 8 \
  --disable-flashinfer-autotune \
  --tool-call-parser glm47 \
  --enable-auto-tool-choice \
  --reasoning-parser glm47
```

**SGLang**（来源 [`../practice/sglang.md`](../practice/sglang.md)）

**p5.48xlarge（8×H100 80GB） · 策略 `high-throughput` · cookbook 状态：verified** · [cookbook 原始配置](https://docs.sglang.io/cookbook/autoregressive/GLM/GLM-5.3-Flash#hw=h100&strategy=high-throughput&quant=fp8&pdMode=unified&kvDsaPair=bf16-tilelang&bcg=off&mmTransport=auto&hicache=off&parsers=auto)

```bash
sglang serve \
  --model-path zai-org/GLM-5.3-Flash \
  --tp-size 8 \
  --ep-size 8 \
  --mem-fraction-static 0.75 \
  --dsa-prefill-backend tilelang \
  --dsa-decode-backend tilelang \
  --kv-cache-dtype bfloat16 \
  --moe-runner-backend deep_gemm \
  --mamba-full-memory-ratio 0.9 \
  --host 0.0.0.0 \
  --port 30000 \
  --reasoning-parser auto \
  --tool-call-parser auto
```

## 压测命令

客户端与服务端在同一台实例上。`<PORT>`：vLLM 8000，SGLang 30000，TrnRT 8000，vLLM-Omni 8091。

```bash
# W1 对话：1024 输入 / 256 输出
python3 bench/llm_bench.py --base-url http://127.0.0.1:<PORT>/v1 --model zai-org/GLM-5.3-Flash \
  --input-len 1024 --output-len 256 --concurrency 1,8,32,64 \
  --label "<框架 版本> / p5.48xlarge / FP8（原生权重） / W1" --out results/glm-5.3-flash_p5/<框架>_w1_1024_256
# W2 长输入：8192 输入 / 1024 输出
python3 bench/llm_bench.py --base-url http://127.0.0.1:<PORT>/v1 --model zai-org/GLM-5.3-Flash \
  --input-len 8192 --output-len 1024 --concurrency 1,8,32,64 \
  --label "<框架 版本> / p5.48xlarge / FP8（原生权重） / W2" --out results/glm-5.3-flash_p5/<框架>_w2_8192_1024
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
