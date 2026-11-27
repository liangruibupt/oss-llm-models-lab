# Benchmark: `mock` @ http://127.0.0.1:18765/v1

- label: mock server (ttft=50ms, itl=10ms), not a real model
- endpoint: chat, input_len: 1024, output_len: 64, ignore_eos: True, started: 2026-11-27T03:00:37Z

| Concurrency | OK/Total | Req/s | Output tok/s | TTFT p50 (ms) | TTFT p99 (ms) | TPOT p50 (ms) | TPOT p99 (ms) | ITL p50 (ms) | ITL p99 (ms) | Mean in/out tok |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 16/16 | 1.46 | 93.1 | 50.8 | 51.0 | 10.09 | 10.14 | 10.08 | 10.56 | 1024/64 |
| 8 | 32/32 | 11.63 | 744.4 | 51.5 | 52.7 | 10.09 | 10.12 | 10.08 | 10.19 | 1024/64 |
| 32 | 128/128 | 46.33 | 2965.1 | 51.2 | 53.1 | 10.09 | 10.11 | 10.08 | 10.23 | 1024/64 |
| 64 | 256/256 | 91.74 | 5871.3 | 51.8 | 59.1 | 10.09 | 10.17 | 10.08 | 10.41 | 1024/64 |
