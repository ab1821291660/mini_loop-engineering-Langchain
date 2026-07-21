

conda create -n 58langchain313 python=3.13




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
