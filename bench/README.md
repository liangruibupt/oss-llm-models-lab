# ⏱ bench：OpenAI 兼容端点压测工具

框架无关：只要服务端实现了带 SSE 流式输出的 `/v1/chat/completions` 或 `/v1/completions`（SGLang、vLLM、vLLM-Omni 的文本路径、TrnRT 等），都能用。只依赖 Python 3.10+ 标准库，新开的实例上可以直接跑。

| 文件 | 作用 |
|---|---|
| [`llm_bench.py`](llm_bench.py) | 压测主程序 |
| [`mock_server.py`](mock_server.py) | 本地 OpenAI 兼容 mock 服务（固定 TTFT / 逐 token 间隔，只绑定 127.0.0.1） |
| [`test_llm_bench.py`](test_llm_bench.py) | 单元测试（对着 mock 服务跑） |
| [`sample/`](sample/) | 对 mock 服务跑出的示例输出（**不是真实模型数据**） |

## 指标定义

| 指标 | 定义 |
|---|---|
| TTFT | 发出请求到收到第一个带文本的流式 chunk（ms）。`content`、`reasoning_content` 都算 |
| TPOT | (端到端延迟 − TTFT) / (输出 token 数 − 1)（ms） |
| ITL | 相邻两个带文本 chunk 的时间间隔（ms）。服务端把多个 token 合进一个 chunk 时，ITL 会大于 TPOT |
| 输出 tok/s | 该并发级别所有成功请求的输出 token 总数 / 该级别墙钟时长 |
| 请求/s | 成功请求数 / 该级别墙钟时长 |

输出 token 数优先取服务端 `usage.completion_tokens`（请求里带 `stream_options.include_usage`），没有时退回 chunk 计数。每项给 mean / p50 / p90 / p99。

## 用法

```bash
python bench/llm_bench.py \
  --base-url http://127.0.0.1:8000/v1 \
  --model openai/gpt-oss-120b \
  --input-len 1024 --output-len 256 \
  --concurrency 1,8,32,64 \
  --label "vLLM 0.34 / p5.48xlarge / MXFP4 / TP8" \
  --out results/gpt-oss-120b_vllm_p5
```

生成 `results/gpt-oss-120b_vllm_p5.json`（完整数据）和 `.md`（汇总表）；有失败请求时退出码为 1。

常用参数：

| 参数 | 说明 |
|---|---|
| `--endpoint chat\|completions` | 默认 `chat` |
| `--input-len` | 输入长度。默认按「1 个常用英文单词 ≈ 1 token」拼接；装了 `transformers` 时加 `--tokenizer <hf_id>` 可精确到 token；实际长度以服务端 `usage.prompt_tokens` 为准，记录在 `mean_prompt_tokens` |
| `--output-len` | `max_tokens`；默认同时发送 `ignore_eos` 与 `min_tokens`（vLLM / SGLang 扩展参数）以固定输出长度。服务端不认这两个参数时加 `--no-ignore-eos` |
| `--num-requests` | 每个并发级别的请求数；0 表示自动 = 4 × 并发，至少 16 |
| `--warmup` | 每个级别先发的不计时请求数（默认 2） |
| `--extra-body` | 合并进每个请求体的 JSON，例如 `'{"modalities": ["text"]}'` |
| `--api-key-env` | 存放 Bearer token 的环境变量名（默认 `OPENAI_API_KEY`，可不设） |

## 本地测试

```bash
python3 -m unittest discover -s bench -v
```

不需要 GPU，也不需要网络。测试会在随机端口起 mock 服务，检查单请求计时、chat 与 completions 两种端点、多并发级别的 JSON/Markdown 输出、并发 64 无失败、HTTP 500 与连不上服务时的错误统计和退出码。

手动试跑：

```bash
python bench/mock_server.py --port 18765 --ttft 0.05 --itl 0.01 &
python bench/llm_bench.py --base-url http://127.0.0.1:18765/v1 --model mock \
  --input-len 1024 --output-len 64 --concurrency 1,8,32,64 --out bench/sample/mock_c1-64
```

结果见 [`sample/mock_c1-64.md`](sample/mock_c1-64.md)：mock 的 TTFT 设为 50 ms、token 间隔 10 ms，测得 TTFT p50 ≈ 51 ms、TPOT p50 ≈ 10.1 ms，说明计时逻辑正确。
