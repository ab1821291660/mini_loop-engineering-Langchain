# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A teaching demo of **loop engineering**: improving an agent by wrapping it in a
`run → verify → improve → retry` outer loop instead of one-shot prompting. Deep
Agents (`create_deep_agent`) is the real coding harness; the loop rewrites *how it
is configured* when verification fails. It is a lab, not a production coding agent.

The repository root is `coding_agent_loop/` — run all commands from there.

## Commands

```bash
uv sync                              # install deps into .venv
cp .env.example .env                 # then set OPENAI_API_KEY=...

# Web UI (primary surface) — http://127.0.0.1:8765
uv run python -m uvicorn app:app --reload --port 8765

# CLI — same improvement loop, prints iterations to stdout
uv run python mainCLI.py

# LangGraph Studio — exposes improve_loop + coding_agent graphs
uv run langgraph dev --port 2025 --no-browser

# Run the seed repo's pytest suite directly (all three should FAIL until fixed)
uv run python -m pytest seed_repo/tests -q
uv run python -m pytest seed_repo/tests/test_pricing.py -q   # single ticket
```

There is no lint step and no test suite for the framework code itself; the only
tests are the intentionally-failing fixtures in `seed_repo/tests/`.

## Architecture

The system runs two nested loops. Understanding the harness/config split is the key
to this codebase.

**Inner loop — one bug ticket through the harness** (`agent_harness.run_task`):
1. `seed_workspace.materialize_workspace` copies `seed_repo/` into a fresh temp dir.
2. `agent_graph.make_agent` builds a Deep Agent over that dir. Backend is chosen by
   config: `LocalShellBackend` (can run pytest via `execute`) when
   `enable_shell=True`, else `FilesystemBackend` (read/write files only).
3. The agent is invoked with the ticket's `request` text.
4. `grader.grade_workspace` verifies the result.

**Outer loop — improvement** (`loop.run_improvement_loop`, mirrored in
`loop_graph.py` as a LangGraph): run all tickets → compute pass rate → if below
target, feed failing traces to `improver.propose_config` which rewrites the config →
retry, up to `max_iterations`.

### Harness vs Config — the central distinction
- **Harness** = Deep Agents itself (planning, filesystem, optional shell). Fixed.
- **Config** = `HarnessConfig` in `harness_config.py`: just two knobs,
  `system_prompt` and `enable_shell`. This is the *only* thing the outer loop
  mutates. `INITIAL_CONFIG` is **deliberately broken** (shell off + a prompt that
  forbids reading tests / running pytest) so iteration 1 fails and the loop has work.

### Verification is process + outcome, not just green tests (`grader.py`)
A capable model can guess a source fix without running anything, so pytest-green
alone is not enough. A ticket only passes if ALL hold:
- `read_file` was called on the failing test (`task.test_path`),
- pytest was actually run via `execute` (requires `enable_shell`),
- the implicated production module (`task.expected_edit_substr`) was edited,
- protected test files are byte-identical to seed (anti-cheat, see `SEED_FILES`),
- pytest passes.

This is *why* the weak starter config cannot pass: with shell disabled it physically
cannot run pytest, so verification fails regardless of the code it writes.

### Component map (`src/`)
- `benchmark.py` — `BENCHMARK`: three symptom-only `BugTicket`s (pricing, invoice,
  refund). Tickets carry `test_path`, `expected_edit_substr`, `protected_paths`.
- `seed_workspace.py` — copies/reads the seed repo; `SEED_FILES` is the canonical
  before-state used for diffing and anti-cheat checks.
- `agent_graph.py` — `make_agent` + `DEEP_AGENT_HARNESS` descriptor; `graph` here is
  the Studio `coding_agent`. Also parses tool calls out of messages
  (`tools_from_messages`, and read/execute extraction happens in `agent_harness.py`).
- `improver.py` — LLM call (`propose_config`) that reads failing traces and returns a
  full replacement `system_prompt` + `enable_shell`.
- `trace_store.py` — appends per-ticket traces to `data/traces.jsonl`; persists the
  latest config to `data/harness.json`.
- `loop.py` (CLI/plain-Python loop) and `loop_graph.py` (LangGraph equivalent) are
  two implementations of the *same* outer loop — keep them in sync when changing loop
  behavior. `langgraph.json` maps `improve_loop`→`loop_graph.py`,
  `coding_agent`→`agent_graph.py`.

### Surfaces share the same core
`app.py` (FastAPI: `/api/bootstrap`, `/api/traces`, `/api/run-loop`; serves
`web/static/`), `main.py` (CLI), and `loop_graph.py` (Studio) are three front-ends
over the same `run_task` / `grade_workspace` / `propose_config` primitives. Business
logic lives in `src/`; the surfaces only orchestrate and present.

## Conventions & gotchas

- The tricky-by-design pieces (weak `INITIAL_CONFIG`, the process-not-just-outcome
  grader) are load-bearing for the demo — don't "fix" them into something that passes
  on iteration 1.
- `seed_repo/tests/` are fixtures that *should* fail on a clean checkout. Never edit
  them to make them pass; the grader treats any change to protected tests as cheating.
- Each ticket runs in its own temp workspace (`tempfile.mkdtemp`); these are not
  cleaned up. The user's own repo files are never touched.
- Model is `openai:gpt-4.1-mini` by default (`AGENT_MODEL`); the same model runs both
  the coding agent and the improver.

## Environment

| Variable | Default | Purpose |
|----------|---------|---------|
| `OPENAI_API_KEY` | — | Required |
| `AGENT_MODEL` | `openai:gpt-4.1-mini` | Agent + improver model |
| `MAX_ITERATIONS` | `3` | Outer loop cap |
| `TARGET_PASS_RATE` | `0.9` | Stop when reached |
| `RESET_TRACES` | `1` | Clear `data/traces.jsonl` on CLI start |
