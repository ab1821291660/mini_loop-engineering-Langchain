

关键坑:结构化输出
deepseek-v4-flash 是思考(reasoning)模型,不支持 function-calling 强制 tool_choice(报错 Thinking mode does not support this tool_choice)。
因此 improver 的结构化输出从 function_calling 改为 json_mode,并在提示词中显式声明 JSON 输出字段。
三个入口验证结果(均用 conda activate 58langchain313 环境)
入口	    命令              	                          结果   
CLI     python mainCLI.py                              ✅ 完整跑通:agent(DeepSeek)执行 → grader 判定 → improver(DeepSeek)重写配置
Web     uvicorn  app:app --port 9999  8765                    ✅ /api/bootstrap 返回 deepseek-v4-flash;POST /api/run-loop 完整跑通循环
                    Quick start
                    cd coding_agent_loop
                    uv sync
                    cp .env.example .env   # set OPENAI_API_KEY=...
                uv run python -m uvicorn app:app --reload --port 8765
                http://localhost:9999/
                Open http://127.0.0.1:8765 → See the loop run → Reset weak config → Run loops.
                Expect:
                Iteration 1 — fails (no shell → cannot execute pytest)
                Improver — turns enable_shell on and rewrites system_prompt
                Later iterations — agent reads tests, runs pytest, fixes code, climbs pass rate
Studio  langgraph dev 的 improve_loop、coding_agent     ✅ 两个图均成功构建(CompiledStateGraph)
                uv run langgraph dev --port 2025 --no-browser
                langgraph dev --config ./langgraph.json --port 2025 --no-browser
            set PYTHONUTF8=1 
            langgraph dev --port 2025
                Open: https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2025
                服务器启动后，你可以通过API文档地址（如 http://127.0.0.1:2025/docs）或 LangGraph Studio UI 来测试你的应用
            - 🚀 API: http://127.0.0.1:2025
              - 🎨 Studio UI: https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2025
              - 📚 API Docs: http://127.0.0.1:2025/docs
  另外还单独做了 DeepSeek 直连连通性测试(返回 pong)和 improver 结构化输出测试(正确返回 enable_shell 与 rationale),均通过。
  ##===================================

conda create -n 58langchain313 python=3.13
conda activate 58langchain313
cursor中搜索框-配置环境::Python: Select Interpreter
pip install --upgrade pip
pip install -r requirements.txt
pip freeze > requirements.txt----pip list --format=freeze > requirements.txt
场景          	命令	                                                                            说明
国内加速（清华源）pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple	   解决网络慢或超时问题，强烈推荐
升级已安装的包	pip install -r requirements.txt --upgrade 或 -U	   强制将已存在的包更新到文件中指定的最新版本
离线/无缓存安装	pip install -r requirements.txt --no-cache-dir   	绕过本地缓存，解决缓存损坏导致的安装失败
指定额外索引源	pip install -r requirements.txt --extra-index-url https://download.pytorch.org/whl/cu118	   适用于 PyTorch 等需要指定专用源的情况
用户级安装（无管理员权限）	pip install -r requirements.txt --user	   仅在无法写入系统目录时使用（Conda 环境一般不需要）



三表面、单内核 —— 业务全在 src/，Web/CLI/Studio 只编排
         loop.py 与 loop_graph.py 双实现 —— 需保持行为同步
app.py / main.py / langgraph.json# 三条入口表面 ##===================================
入口	    启动方式
CLI     python main.py
Web     uvicorn app:app --port 8765（/ 故事页，/demo 交互）  +Web POST /api/run-loop 为例
Studio  langgraph dev（图：improve_loop、coding_agent）
##
##
每张工单在临时目录 copytree(seed_repo)，不污染用户仓库。产物写入 data/traces.jsonl、data/harness.json。 ##===================================
##
##
verify → improve → verify ##===================================
一句话总结：
用 Deep Agents 作固定 coding harness，用 pytest + 过程检查 作验证信号，用 LLM 改写 HarnessConfig 作改进步，
在 Web / CLI / LangGraph Studio 演示同一条 Level-4 hill-climbing loop；业务在 src/，缺陷在 seed_repo/，刻意弱启动配置以驱动外层改进。
若需要，我可以再按模块（如 grader / improver / 前端）做更细的源码级拆解。
具体故事（Acme Commerce）：
   给 Deep Agents 一个有 bug 的包：seed_repo/acme_billing
   下发 3 张症状型工单（BENCHMARK）
   Agent 用文件系统工具（可选 shell）尝试修复
   Grader 做过程 + 结果双重验证
   失败则 Improver 根据 trace 改写配置（system_prompt + enable_shell）
   重跑，直到通过率达标或达到最大迭代次数
局限：非生产（无权限/多租户）、配置旋钮极少、/api/run-loop 同步阻塞、临时目录不清理、Improver prompt 偏“剧透”指向 enable_shell=true。




##三张工单与 seed 缺陷：：症状型工单 —— 不给公式，逼 agent 调查
Ticket	           症状	          根因文件
pricing-discount   百分比折扣错    pricing.py：amount - percent
invoice-total      多数量少计费    invoices.py：忽略 quantity
partial-refund     部分退款超额    refunds.py：未 clamp 剩余额度
##===================================
Grader 全部满足才算 pass：：过程型验证 —— 强迫读测试 + 开 shell + 跑 pytest
读过对应测试文件（read_file）
通过 execute 跑过 pytest（需要 enable_shell）
改过期望生产模块
受保护测试与 seed 字节级一致（防改测试作弊）
当前 workspace 上 pytest 通过
因此关 shell 时，即使“猜对代码”也会失败——这是刻意的 anti-cheat / 教学机制。
##===================================
概念	              含义                                      代码
Harness（固定）    Deep Agents：规划、文件系统、可选 shell     create_deep_agent
Config（可改进）   外层唯一会改的旋钮                          system_prompt、enable_shell
刻意设计：INITIAL_CONFIG 很弱（关 shell、禁止读测试/跑 pytest），第 1 轮几乎必败，外层循环才有改进空间。##===================================
Harness 固定、Config 可变 —— 外层只改两个旋钮，焦点清晰----弱初始配置不可“修好” —— 保证第 1 轮失败，驱动 L4 循环。##===================================



# 参考代码：
# 参考代码：
git:https://github.com/Frontier-Intelligence-Lab/Loop-engineering-demo-Langchain-
# Loop Engineering — Coding Agent
## What is this repo?
A **teaching demo** of [loop engineering](https://www.langchain.com/blog/the-art-of-loop-engineering): how you build better agents by wrapping them in **run → verify → improve → retry**, not by one-shot prompting.

It is **not** a production coding agent product. It is a small, runnable lab that shows the pattern end-to-end with LangChain’s real agent harness (**Deep Agents**) and a real verification signal (**pytest + process checks**).

## What is it doing?

1. **Gives Deep Agents a buggy Python package** (`seed_repo/acme_billing`) and three support-style bug tickets  
2. **Lets the agent try to fix the code** using Deep Agents tools (filesystem; shell when enabled)  
3. **Grades the result** — not only pytest green, but also process:
   - must `read_file` the failing test  
   - must `execute` pytest in the workspace  
   - must edit the implicated production module  
   - tests must stay intact  
4. **If it fails, rewrites harness config** (`system_prompt` + `enable_shell`) from the failing traces  
5. **Runs again** until pass rate hits the target or max iterations  

That outer cycle is the loop. Deep Agents is the harness doing the work; the loop is how you improve how that harness is configured.

Starter config is **intentionally weak** (`enable_shell=false` + a bad process prompt). A smart model can still guess a code fix from source — but without shell it cannot run pytest, so **iteration 1 fails verification** and the improvement loop has something to do.

## What you see in the UI
Open **http://127.0.0.1:8765** for the **Acme Commerce** story landing page, then **Open demo** (or go to **/demo**) for the interactive loop.
On the demo, for **each iteration** and **each ticket**, the UI shows:
- pass / fail + grader feedback  
- tools used, files read, files edited, shell commands  
- pytest output tail  
- **Repo after this ticket** — before (seed) → after (agent edit) for every changed file  
- config rewrite rationale when the improver runs
The side panel **Seed repo** is the starting buggy checkout. Per-iteration diffs live under **What happened**.
## Harness vs config
| Term | What it is |
|------|------------|
| **Harness** | Deep Agents (`create_deep_agent`) — planning, filesystem, optional shell |
| **Config** | `system_prompt` + `enable_shell` — knobs the improvement loop rewrites |
| **Verify** | `pytest` + process checks (read test, execute pytest, edit right module) |
| **Improve** | Failing traces → rewrite config → retry |
Deep Agents *is* the harness. This demo does not invent a fake harness from text boxes.
## Quick start
```bash
cd coding_agent_loop
uv sync
cp .env.example .env   # set OPENAI_API_KEY=...
uv run python -m uvicorn app:app --reload --port 8765
```
Open **http://127.0.0.1:8765** → **See the loop run** → **Reset weak config** → **Run loops**.  ##===================================##===================================
Expect:
1. **Iteration 1** — fails (no shell → cannot execute pytest)  
2. **Improver** — turns `enable_shell` on and rewrites `system_prompt`  
3. **Later iterations** — agent reads tests, runs pytest, fixes code, climbs pass rate  





## How one outer loop works
1. Copy `seed_repo/` into a temp workspace  
2. Deep Agents works the bug ticket (FS tools; shell only if `enable_shell`)  
3. Grader checks process + pytest + locked tests  
4. UI records before/after repo files for that ticket  
5. If pass rate &lt; target → `improver.py` rewrites config → repeat  

## Bug tickets (`seed_repo/acme_billing`)
```bash
uv run python -m pytest seed_repo/tests -q  ##===================================##===================================
```
| Ticket | Symptom |
|--------|---------|
| `pricing-discount` | Percentage discounts look wrong |
| `invoice-total` | Multi-quantity lines undercharge |
| `partial-refund` | Partial refunds can over-refund |
Tickets are symptom-only (no spoon-fed formulas). Verification still requires reading the test and running pytest — a lucky source-only guess is not enough.





## Project layout
```
coding_agent_loop/
├── app.py                 # FastAPI: / story, /demo loop UI, /api/run-loop
├── main.py                # CLI: same improvement loop
├── seed_repo/             # Buggy acme_billing + tests
├── web/static/            # Landing + demo UI
├── data/                  # traces.jsonl + last harness config
└── src/
    ├── agent_graph.py     # create_deep_agent + FS / LocalShell backend
    ├── agent_harness.py   # Run one ticket
    ├── benchmark.py       # Bug tickets
    ├── grader.py          # pytest + process verification
    ├── harness_config.py  # system_prompt + enable_shell
    ├── improver.py        # Rewrite config from failures
    ├── loop.py            # run_improvement_loop()
    └── loop_graph.py      # Studio graph: improve_loop
```

## CLI
```bash
uv run python mainCLI.py ##===================================##===================================
```
## LangGraph Studio
```bash
uv run langgraph dev --port 2025 --no-browser ##===================================##===================================
```
Open: [https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2025](https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2025)

| Graph | Role |
|-------|------|
| `improve_loop` | Full loop: run → verify → rewrite config → retry | ##===================================##===================================
| `coding_agent` | Single Deep Agents coding run |

Example input for `improve_loop`:
```json
{ "max_iterations": 3, "target_pass_rate": 0.9 }
```

## Environment
| Variable | Default | Purpose |
|----------|---------|---------|
| `OPENAI_API_KEY` | — | Required |
| `AGENT_MODEL` | `openai:gpt-4.1-mini` | Agent + improver model |
| `MAX_ITERATIONS` | `3` | Outer loop cap |
| `TARGET_PASS_RATE` | `0.9` | Stop when reached |
| `RESET_TRACES` | `1` | Clear `data/traces.jsonl` on CLI start |

## Reading

- [Deep Agents overview](https://docs.langchain.com/oss/python/deepagents/overview)
- [The Art of Loop Engineering](https://www.langchain.com/blog/the-art-of-loop-engineering)
- [`SPEC.md`](./SPEC.md)
