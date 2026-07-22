"""Outer improvement loop: Deep Agents coding step2agentHarness → pytest → rewrite prompt."""

from __future__ import annotations
from pathlib import Path

from src.step2agentHarness.agent_harness import run_task
from src.step1trigger.benchmark import BENCHMARK
from src.step3evaluate.grader import grade_workspace
from src.skill.harness_config import HarnessConfig, clone_config
from src.step5evolver.improver import propose_config
from src.step4state.trace_store import append_traces, get_failures, save_harness
class IterationResult:
    def __init__(
        self,
        iteration: int,
        passed: int,
        total: int,
        config: HarnessConfig,
        rationale: str | None = None,
    ):
        self.iteration = iteration
        self.passed = passed
        self.total = total
        self.pass_rate = passed / total if total else 0.0
        self.config = config
        self.rationale = rationale
    def __repr__(self) -> str:#IterationResult的__repr__(self)方法
        return (
            f"Iteration {self.iteration}: {self.passed}/{self.total} "
            f"({self.pass_rate:.0%})"
        )
def run_improvement_loop(
    initial_config: HarnessConfig,
    model: str,
    max_iterations: int,#3
    target_pass_rate: float,#0.9
) -> tuple[list[IterationResult], HarnessConfig]:
    current = clone_config(initial_config)##========
    save_harness(current.snapshot())##========


    results: list[IterationResult] = []
    for iteration in range(1, max_iterations + 1):
        print(f"\n--- Iteration {iteration} ---")
        print(f"Deep Agents config (enable_shell={current.enable_shell}):")
        print(current.system_prompt)


        traces: list[dict] = []
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
            trace = {
                "iteration": iteration,
                "task_id": task.id,
                "request": task.request,
                "failure_hint": task.failure_hint,

                "edited_paths": raw["edited_paths"],
                "read_paths": raw["read_paths"],
                "tools_called": raw.get("tools_called") or [],
                "execute_commands": raw.get("execute_commands") or [],
                "final_message": raw["final_message"],

                "verdict": grade.verdict,
                "feedback": grade.feedback,
                "checks": grade.checks,
                "pytest_output": grade.pytest_output,

                "config": current.snapshot(),
            }
            traces.append(trace)
            marker = "PASS" if grade.verdict == "pass"    else "FAIL"
            print(f"  [{marker}] {task.id}: {grade.feedback}")##===================================##===================================##===================================##===================================
            if grade.verdict == "pass":
                passed += 1
        append_traces(traces)##========
        ##
        ##
        result = IterationResult(
            iteration,
            passed,
            len(BENCHMARK),
            clone_config(current)
        )
        results.append(result)
        print(result)#默认走，IterationResult的__repr__(self)方法
        print(result.__str__())




        if result.pass_rate >= target_pass_rate:#0.9##===================================
            print("Target pass rate reached.")
            break




        failures = get_failures(iteration)##===================================##===================================
        if not failures:
            print("No failures to learn from; stopping early.")
            break




        #此配置更改的目标故障模式。
        current, rationale = propose_config(failures, current, model)##===================================##===================================
        save_harness(current.snapshot())##========
        results[-1].rationale = rationale#此配置更改的目标故障模式。
        print(f"Config rewrite rationale: {rationale}")#此配置更改的目标故障模式。##===================================##===================================##===================================##===================================
    return results, current
