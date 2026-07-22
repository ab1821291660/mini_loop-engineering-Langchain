"""Loop Engineering App — Deep Agents coding harness + pytest + improvement.
Use case: fix real bugs in acme_billing. + Verification is pytest.

Run:
    uv run uvicorn app:app --reload --port 8765
"""

from __future__ import annotations
import os
from pathlib import Path
from typing import Any
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from src.step2agentHarness.agent_graph import DEEP_AGENT_HARNESS
from src.step1trigger.benchmark import BENCHMARK
from src.step2agentHarness import run_task
from src.step3evaluate.grader import grade_workspace
from src.skill.harness_config import INITIAL_CONFIG, HarnessConfig, clone_config
from src.step5evolver.improver import propose_config
from src.step2agentHarness.seed_workspace import SEED_FILES
from src.step4state.trace_store import append_traces, clear_traces, load_all_traces, save_harness
load_dotenv()
ROOT = Path(__file__).parent
STATIC = ROOT / "web" / "static"
app = FastAPI(title="Loop Engineering", version="0.4.0")
app.mount("/static", StaticFiles(directory=STATIC), name="static")


def _repo_view(repo: dict[str, str], edited_paths: list[str]) -> dict[str, Any]:
    """Before/after file view for the UI (seed → step2agentHarness workspace)."""
    files: dict[str, Any] = {}
    for path in sorted(edited_paths or []):
        before = SEED_FILES.get(path)
        after = repo.get(path)
        files[path] = {
            "before": before,
            "after": after,
            "changed": before != after,
        }
    return {
        "edited_paths": list(edited_paths or []),
        "files": files,
    }


def _default_model() -> str:
    return os.getenv("AGENT_MODEL", "openai:gpt-4.1-mini")


def _config_from_req(
    system_prompt: str | None,
    enable_shell: bool | None,
) -> HarnessConfig:
    return HarnessConfig(
        system_prompt=system_prompt or INITIAL_CONFIG.system_prompt,
        enable_shell=(
            INITIAL_CONFIG.enable_shell if enable_shell is None else enable_shell
        ),
    )

class RunRequest(BaseModel):
    system_prompt: str | None = None
    enable_shell: bool | None = None
    model: str | None = None
    max_iterations: int = Field(default=3, ge=1, le=5)
    target_pass_rate: float = Field(default=0.9, ge=0.0, le=1.0)
    reset_traces: bool = True





@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC / "index.html")

@app.get("/demo")
def demo() -> FileResponse:
    return FileResponse(STATIC / "demo.html")

@app.get("/api/bootstrap")
def bootstrap() -> dict[str, Any]:
    return {
        "definition": (
            "Deep Agents is the coding harness. Starter config is weak "
            "(no shell, skip tests). Verification requires: read the failing "
            "test, run pytest via execute, edit the right module, and go green. "
            "Iteration 1 should fail; the loop then rewrites config and retries."
        ),
        "use_case": (
            "Acme Commerce — bugfix coding step2agentHarness; pytest + process checks grade each ticket"
        ),
        "harness": DEEP_AGENT_HARNESS,
        "config": INITIAL_CONFIG.snapshot(),
        "model": _default_model(),##========
        "max_iterations": int(os.getenv("MAX_ITERATIONS", "3")),
        "target_pass_rate": float(os.getenv("TARGET_PASS_RATE", "0.9")),
        "tasks": [
            {
                "id": t.id,
                "title": t.title,
                "request": t.request,
                "test_path": t.test_path,
                "failure_hint": t.failure_hint,
            }
            for t in BENCHMARK
        ],
        "seed_docs": SEED_FILES,
    }


@app.get("/api/traces")
def get_traces() -> dict[str, Any]:
    return {"traces": load_all_traces()}


@app.post("/api/run-loop")
def api_run_loop(body: RunRequest) -> dict[str, Any]:##========  ##===================================
    if not os.getenv("OPENAI_API_KEY"):
        raise HTTPException(400, "OPENAI_API_KEY is not set in .env")
    if body.reset_traces:
        clear_traces()##========

    current = clone_config(_config_from_req(body.system_prompt, body.enable_shell))##========
    model = body.model or _default_model()##========
    history: list[dict[str, Any]] = []
    stop_reason = "max iterations reached"
    initial = current.snapshot()

    for iteration in range(1, body.max_iterations + 1):##===================================
        task_results: list[dict[str, Any]] = []
        passed = 0
        for task in BENCHMARK:##===================================
            raw = run_task(task, current, model)##===================================



            grade = grade_workspace(##===================================
                task,
                Path(raw["workspace"]),
                tools_called=raw.get("tools_called") or [],
                read_paths=raw.get("read_paths") or [],
                execute_commands=raw.get("execute_commands") or [],
            )
            row = {
                "iteration": iteration,
                "task_id": task.id,
                "request": task.request,
                "failure_hint": task.failure_hint,

                "edited_paths": raw["edited_paths"],
                "read_paths": raw["read_paths"],
                "tools_called": raw.get("tools_called") or [],
                "execute_commands": raw.get("execute_commands") or [],
                "final_message": (raw["final_message"] or "")[:400],

                "verdict": grade.verdict,
                "feedback": grade.feedback,
                "checks": grade.checks,
                "pytest_output": grade.pytest_output[-1200:],
                "repo": _repo_view(raw["repo"], raw.get("edited_paths") or []),##========
                "config": current.snapshot(),
            }
            task_results.append(row)
            if grade.verdict == "pass":##========
                passed += 1
        append_traces(task_results)##========
        ##
        ##
        total = len(BENCHMARK)
        pass_rate = passed / total if total else 0.0
        entry = {
            "iteration": iteration,
            "passed": passed,
            "total": total,
            "pass_rate": pass_rate,
            "config": current.snapshot(),
            "task_results": task_results,
            "improve_rationale": None,
        }




        if pass_rate >= body.target_pass_rate:
            stop_reason = f"target reached ({pass_rate:.0%} ≥ {body.target_pass_rate:.0%})"
            history.append(entry)
            save_harness(current.snapshot())##========
            break

        failures = [t for t in task_results if t["verdict"] == "fail"]
        if not failures:
            stop_reason = "no failures to learn from"
            history.append(entry)
            save_harness(current.snapshot())##========
            break

        improved, rationale = propose_config(failures,  current,  model)##===================================
        entry["improve_rationale"] = rationale
        history.append(entry)
        current = improved
        save_harness(current.snapshot())##========
    else:
        save_harness(current.snapshot())##========

    return {
        "stop_reason": stop_reason,
        "final_config": current.snapshot(),
        "initial_config": initial,
        "history": history,
        "final_pass_rate": history[-1]["pass_rate"] if history    else 0.0,
    }
## uv run uvicorn app:app --reload --port 8765
# cd coding_agent_loop
# uv sync
# cp .env.example .env   # set OPENAI_API_KEY=...
# uv run python -m uvicorn app:app --reload --port 8765

