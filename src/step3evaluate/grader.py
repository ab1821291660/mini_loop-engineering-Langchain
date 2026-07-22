"""Verification = pytest + process checks (must read tests and run them).

Outcome alone is not enough for this teaching demo: a smart model can guess
fixes from source. Loop engineering needs a verification signal the weak
config cannot satisfy — here: read the failing test + execute pytest.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from pydantic import BaseModel, Field

from src.step1trigger.benchmark import BugTicket
from src.step2agentHarness.seed_workspace import SEED_FILES


def run_pytest(workspace: Path, test_path: str) -> tuple[bool, str]:
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", test_path, "-q", "--tb=short"],
        cwd=workspace,
        capture_output=True,
        text=True,
        timeout=60,
    )
    output = (proc.stdout or "") + (proc.stderr or "")
    return proc.returncode == 0, output.strip()
def _ran_pytest(tools_called: list[str], execute_commands: list[str],    test_path: str) -> bool:
    if "execute" not in set(tools_called or []):
        return False
    needle = test_path.replace("\\", "/")
    for cmd in execute_commands or []:
        c = cmd.lower().replace("\\", "/")
        if "pytest" in c and (needle.lower() in c or "tests/" in c or c.strip().endswith("pytest") or "pytest -q" in c):
            return True
        if "pytest" in c:
            return True
    return False




class Grade(BaseModel):
    verdict: str
    feedback: str
    checks: list[str] = Field(default_factory=list)
    pytest_output: str = ""

def grade_workspace(
    task: BugTicket,
    workspace: Path,
    *,
    tools_called: list[str] | None = None,
    read_paths: list[str] | None = None,
    execute_commands: list[str] | None = None,
) -> Grade:
    checks: list[str] = []
    failures: list[str] = []
    tools = tools_called or []
    reads = {p.lstrip("/") for p in (read_paths or [])}
    # result = set()
    # for p in (read_paths or []):
    #     result.add(p.lstrip("/"))
    commands = execute_commands or []


    # --- Process requirements (this is what makes weak config fail) ---
    test_rel = task.test_path.lstrip("/")
    if test_rel in reads or any(r.endswith(test_rel) or test_rel.endswith(r) for r in reads):
        checks.append(f"read failing test: {test_rel}")
    else:
        failures.append(
            f"did not read_file on {test_rel} before claiming a fix "
            f"(read: {sorted(reads) or 'none'})"
        )


    if _ran_pytest(tools, commands, test_rel):##===================================##===================================##===================================
        checks.append("ran pytest via execute")
    else:
        failures.append(
            "did not execute pytest in the workspace "
            "(enable_shell + `python -m pytest …` required)"
        )


    # Anti-cheat: protected tests must still exist and match seed content.
    for rel in task.protected_paths:
        path = workspace / rel
        if not path.is_file():
            failures.append(f"deleted protected test file: {rel}")##===================================
            continue
        current = path.read_text(encoding="utf-8")
        seed = SEED_FILES.get(rel, "")##========
        if current != seed:
            failures.append(f"modified protected test file: {rel}")##===================================
        else:
            checks.append(f"tests intact: {rel}")
    # Must edit the implicated production module (not just README).
    expected = task.expected_edit_substr.lstrip("/")
    edited = {
        p.relative_to(workspace).as_posix()
        for p in workspace.rglob("*")
        if p.is_file()
        and "__pycache__" not in p.parts
        and ".pytest_cache" not in p.parts
        and SEED_FILES.get(p.relative_to(workspace).as_posix()) != p.read_text(encoding="utf-8", errors="ignore")
    }
    if any(expected in p for p in edited):
        checks.append(f"edited production code: {expected}")
    else:
        failures.append(f"did not edit required module containing {expected!r}")


    ok, output = run_pytest(workspace, task.test_path)##===================================##===================================##===================================
    if ok:
        checks.append(f"pytest passed: {task.test_path}")
    else:
        failures.append(f"pytest failed: {task.test_path}")
        tail = "\n".join(output.splitlines()[-20:])
        failures.append(tail or "(no pytest output)")


    if failures:
        return Grade(
            verdict="fail",
            feedback="; ".join(failures[:4]),##===================================
            checks=checks,
            pytest_output=output,
        )
    return Grade(
        verdict="pass",
        feedback=f"pytest green + verified process for {task.test_path}",##===================================
        checks=checks,
        pytest_output=output,
    )
