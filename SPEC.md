# Spec: Coding-agent loop engineering
## Use case
Deep Agents acts as a coding harness over `seed_repo/` (buggy `acme_billing`).
Verification is pytest. 
Improvement rewrites `system_prompt` + `enable_shell`.

## Harness vs config
- **Harness** = `create_deep_agent` + filesystem/shell backend
- **Config** = `HarnessConfig` (`system_prompt`, `enable_shell`)

## Surfaces
- Web story: `app.py` → http://127.0.0.1:8765 (`/`)
- Web demo: http://127.0.0.1:8765/demo
- CLI: `main.py`
- Studio: `improve_loop` + `coding_agent` in `langgraph.json`
