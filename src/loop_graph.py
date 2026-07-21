"""Studio graph: improvement loop around the Deep Agents coding harness."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Literal

from dotenv import load_dotenv
from langgraph.graph import END, START, StateGraph
from typing_extensions import NotRequired, TypedDict

from src.agent_harness import run_task
from src.benchmark import BENCHMARK
from src.grader import grade_workspace
from src.harness_config import INITIAL_CONFIG, HarnessConfig
from src.improver import propose_config
from src.trace_store import append_traces, save_harness

load_dotenv()

def _config(state: ImproveLoopState) -> HarnessConfig:
    enable_shell = state.get("enable_shell")##========
    if enable_shell is None:
        enable_shell = INITIAL_CONFIG.enable_shell
    return HarnessConfig(
                        system_prompt=state.get("system_prompt") or INITIAL_CONFIG.system_prompt,##========
                        enable_shell=bool(enable_shell),
    )
class ImproveLoopState(TypedDict, total=False):
    model: NotRequired[str]
    max_iterations: NotRequired[int]
    target_pass_rate: NotRequired[float]

    system_prompt: str
    enable_shell: bool

    iteration: int
    pass_rate: float
    passed: int
    total: int
    status: str
    stop_reason: NotRequired[str]##===================================
    improve_rationale: NotRequired[str]##===================================
    task_results: list[dict[str, Any]]
    history: list[dict[str, Any]]


def init_or_passthrough(state: ImproveLoopState) -> dict[str, Any]:
    updates: dict[str, Any] = {}
    if not state.get("system_prompt"):
        updates["system_prompt"] = INITIAL_CONFIG.system_prompt
    if state.get("enable_shell") is None:
        updates["enable_shell"] = INITIAL_CONFIG.enable_shell
    if not state.get("model"):
        updates["model"] = os.getenv("AGENT_MODEL", "openai:gpt-4.1-mini")
    if state.get("max_iterations") is None:
        updates["max_iterations"] = int(os.getenv("MAX_ITERATIONS", "3"))
    if state.get("target_pass_rate") is None:
        updates["target_pass_rate"] = float(os.getenv("TARGET_PASS_RATE", "0.9"))

    if state.get("iteration") is None:
        updates["iteration"] = 0
    if state.get("history") is None:
        updates["history"] = []
    if state.get("task_results") is None:
        updates["task_results"] = []
    if not state.get("status"):
        updates["status"] = "running"##===================================##===================================
    return updates


def run_and_grade(state: ImproveLoopState) -> dict[str, Any]:
    iteration = int(state.get("iteration") or 0) + 1
    model = state.get("model") or os.getenv("AGENT_MODEL", "openai:gpt-4.1-mini")
    config = _config(state)##========


    task_results: list[dict[str, Any]] = []
    passed = 0
    for task in BENCHMARK:##===================================
        raw = run_task(task, config, model)##===================================




        grade = grade_workspace(
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
            "final_message": (raw["final_message"] or "")[:500],

            "verdict": grade.verdict,
            "feedback": grade.feedback,
            "checks": grade.checks,
            "pytest_output": grade.pytest_output[-1200:],
            "config": config.snapshot(),
        }
        task_results.append(row)
        if grade.verdict == "pass":
            passed += 1
    append_traces(task_results)##========
    ##
    ##
    total = len(BENCHMARK)
    pass_rate = passed / total if total else 0.0
    history = list(state.get("history") or [])
    history.append(
        {
            "iteration": iteration,
            "passed": passed,
            "total": total,
            "pass_rate": pass_rate,##===================================
            "system_prompt": config.system_prompt,
            "enable_shell": config.enable_shell,
        }
    )
    return {
        "iteration": iteration,
        "passed": passed,
        "total": total,
        "pass_rate": pass_rate,
        "task_results": task_results,
        "history": history,
        "status": "running",##===================================
        "improve_rationale": "",##===================================
    }


def rewrite_config(state: ImproveLoopState) -> dict[str, Any]:
    model = state.get("model") or os.getenv("AGENT_MODEL", "openai:gpt-4.1-mini")
    current = _config(state)##========
    failures = [t for t in (state.get("task_results") or []) if t.get("verdict") == "fail"]
    improved, rationale = propose_config(failures,
                                         current,
                                         model)
    save_harness(improved.snapshot())##========
    return {
        "system_prompt": improved.system_prompt,
        "enable_shell": improved.enable_shell,
        "improve_rationale": rationale,
        "status": "improving",
    }


def finalize(state: ImproveLoopState) -> dict[str, Any]:
    target = float(state.get("target_pass_rate") or 0.9)
    max_iterations = int(state.get("max_iterations") or 3)

    iteration = int(state.get("iteration") or 0)
    pass_rate = float(state.get("pass_rate") or 0.0)
    if pass_rate >= target:##===================================
        reason = f"target pass rate reached ({pass_rate:.0%} >= {target:.0%})"
    elif iteration >= max_iterations:##===================================
        reason = f"max iterations reached ({iteration})"
    else:
        reason = "no failures left to learn from"
    save_harness(_config(state).snapshot())##========
    return {"status": "done", ##===================================##===================================
            "stop_reason": reason}




def route_after_grade(state: ImproveLoopState) -> Literal["rewrite_config", "done"]:
    target = float(state.get("target_pass_rate") or 0.9)
    max_iterations = int(state.get("max_iterations") or 3)

    iteration = int(state.get("iteration") or 0)
    pass_rate = float(state.get("pass_rate") or 0.0)

    failures = [t for t in (state.get("task_results") or []) if t.get("verdict") == "fail"]
    if pass_rate >= target or iteration >= max_iterations or not failures:
        return "done"
    return "rewrite_config"
def build_graph():
    g = StateGraph(ImproveLoopState)##===================================##===================================
    g.add_node("init", init_or_passthrough)
    g.add_node("run_and_grade", run_and_grade)
    g.add_node("rewrite_config", rewrite_config)
    g.add_node("done", finalize)


    g.add_edge(START, "init")
    g.add_edge("init", "run_and_grade")
    g.add_conditional_edges(
        "run_and_grade",
        route_after_grade,
        {"rewrite_config": "rewrite_config",   "done": "done"},
    )
    g.add_edge("rewrite_config", "run_and_grade")
    g.add_edge("done", END)
    return g.compile()
graph = build_graph()

