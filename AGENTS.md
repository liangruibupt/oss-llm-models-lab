# AGENTS.md — 给 AI task worker 的首读指引

> 任何在本仓库更新文档、跑压测的 agent，动手前先读这份文件。

## 这个仓库是什么
开源权重 LLM × 推理框架（SGLang、vLLM、TrnRT、vLLM-Omni、DeepInfer）的支持矩阵、AWS 实践命令、已公布性能汇总，以及一个框架无关的 OpenAI 兼容压测工具。文档用中文，表格为主，章节标题带 emoji，每个文档都要在 README 的文档索引里有链接。

## 固定约定（改动前不要自作主张换掉）
- **框架顺序**：SGLang → vLLM → TrnRT → vLLM-Omni → DeepInfer，所有表格都按这个顺序。
- **单元格符号**：✅ 官方支持（必须链到文档 / recipe / cookbook / PR）；🟡 部分/实验/社区/只支持同系列旧型号（写明是哪种）；❌ 不支持；➖ 不适用。每个 ✅/🟡 都要有来源链接，并在文档头部写 `checked YYYY-MM-DD`。
- **性能数字**：只收公开发布的，逐条标注「官方 / 第三方」、来源链接、硬件、精度、负载。**绝不编造或推算数字**；不同来源不放进同一张表比较。
- **引用**：转述，不大段照抄；任何直接引用不超过 30 个词。

## 核对事实的方法（已验证可用）
- 模型是否存在、参数、许可证：HF API `https://huggingface.co/api/models/<id>`，加上 `resolve/main/config.json`、`README.md`、`LICENSE`。
- vLLM：`vllm/model_executor/models/registry.py` 是否注册该架构；[vLLM Recipes](https://recipes.vllm.ai/) 的 JSON API `https://recipes.vllm.ai/<hf_id>.json`（`meta.hardware` 列出有配置的硬件）与 `/<hf_id>/hw/<hw>.json`（渲染好的命令）。部分硬件会 404（例如 Mistral-Large-4 的 `h200`），不要把 404 的条目写进 practice。
- SGLang：`docs/cookbook/autoregressive/<Org>/<Model>.mdx` 是否存在；`python/sglang/cli/_commands/<org>--<model>.json` 有每个硬件的命令和 `verified / in-progress / unverified` 状态；速度数据在 `docs/src/snippets/configs/<org>/<model>-benchmarks.jsx`。
- vLLM-Omni：`docs/models/supported_models.md` 与 `recipes/`。
- TrnRT / DeepInfer：README 的支持列表；DeepInfer 只有离线 `LLM` 接口，没有 HTTP 服务。
- AWS 价格：`aws pricing get-products --region us-east-1 --service-code AmazonEC2`（只读）；trn2 在美国区没有按需价，用 `aws ec2 describe-capacity-block-offerings`（只读）。
- 改完文档后检查所有外链：`curl -s -o /dev/null -L -w '%{http_code}'`，都应是 200。

## 压测
- 工具：`bench/llm_bench.py`（标准库，无依赖）；改了它必须跑 `python3 -m unittest discover -s bench -v`，并检查**它自己的退出码**（不要把测试命令管道给 `tail` 后再用 `&&` 判断）。
- 实测前**必须有成本审批**；按 [`docs/BENCH_PLAN.md`](docs/BENCH_PLAN.md) 的组合与命令执行，结果写入 `results/<model>_<framework>_<instance>.{json,md}`，再更新 PERF 文档（标为「本仓库实测」）。
- 启动命令严格来自 `docs/practice/`；有任何调参都要在结果里写明。

## 实测运行的铁律（2026-11-27 g6e 运行踩过的坑）
- **先取回、核对，再终止**：`scp` 取回结果并在本地 `ls`/读 JSON 确认之后，再**单独一步**跑 `scripts/teardown.py`。两者绝不能同时发起；本地已有的旧副本在新副本核对完之前不要删。那次运行就因为两者并发、实例中途被终止，丢了全部原始 JSON。
- **不要覆盖正在运行的脚本**：bash 是边读边执行的，用 `scp` 覆盖一个正在跑的 `.sh` 会让旧进程执行错乱的命令。改脚本就换个新文件名。
- **按 PID 杀进程**：`pgrep -f <模式>` / `pkill -f` 会匹配到发出命令的那个 ssh shell 自己，把自己杀掉。记下 PID，用 `kill <PID>`。
- **后台任务单独一条命令启动**（`ssh -f ... 'nohup bash x.sh > x.out 2>&1 < /dev/null &'`），状态另起命令轮询。
- **HF 离线模式**：`snapshot_download(revision=<sha>)` 不写 `refs/main`；服务端带 `HF_HUB_OFFLINE=1` 时要手动写，见 [`scripts/box/setup_qwen27b.sh`](scripts/box/setup_qwen27b.sh)。
- **开机用 [`scripts/launch.py`](scripts/launch.py)**：自有 Name tag / key / SG，key 放 `~/.oss-llm-bench/`（不放 scratch）；[`scripts/teardown.py`](scripts/teardown.py) 只终止 Name tag 匹配的实例。绝不停止或终止别的会话的实例。实例上另设 `sudo shutdown -h +N` 兜底（`InstanceInitiatedShutdownBehavior=terminate`）。
- AMI 用 Deep Learning Base OSS Nvidia Driver GPU AMI (Ubuntu 24.04)：vLLM / SGLang 的官方镜像都是 CUDA 13.0 构建，需要新驱动。

## git 规则
- 不能直接 push 到 `main`（受保护）。在 feature 分支上工作：先 `git commit`，再单独一行 `git push origin <feature-branch>`，再 `gh pr create --base main`。
- 仓库工作副本放稳定路径 `/home/ubuntu/workplace/oss-llm-models-lab`，只 `git pull`，不要每次重新 clone 到 scratch。
- PR 合并后用 `gh api repos/liangruibupt/oss-llm-models-lab/git/trees/main?recursive=1` 核对文件真的在 main 上。

## 成本纪律
GPU 实例按小时计费（p5.48xlarge $55.04/h，p6-b300.48xlarge $142.416/h）。**跑完立即终止**，不要挂机；不要动别的会话或别人的实例。
