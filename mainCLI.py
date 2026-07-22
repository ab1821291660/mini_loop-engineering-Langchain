"""CLI entry for the Deep Agents + loop engineering demo."""
import os
from dotenv import load_dotenv
from src.skill.harness_config import INITIAL_CONFIG
from src.loop import run_improvement_loop##===================================
from src.step4state.trace_store import clear_traces##===================================
def main() -> None:
    load_dotenv()

    model = os.getenv("AGENT_MODEL", "openai:gpt-4.1-mini")
    max_iterations = int(os.getenv("MAX_ITERATIONS", "3"))
    target_pass_rate = float(os.getenv("TARGET_PASS_RATE", "0.9"))
    reset = os.getenv("RESET_TRACES", "1") == "1"
    if reset:
        clear_traces()
    print("Loop engineering — coding step2agentHarness on acme_billing")
    print(f"Model: {model}")
    print(f"Max iterations: {max_iterations}")
    print(f"Target pass rate: {target_pass_rate:.0%}")
    print("Harness = Deep Agents (LocalShellBackend).")##===================================
    print("Verify = pytest.\n "##===================================
          "Improve = rewrite system_prompt on failures.\n")##===================================


    results, final_config = run_improvement_loop(
        initial_config=INITIAL_CONFIG,
        model=model,
        max_iterations=max_iterations,
        target_pass_rate=target_pass_rate,
    )
    print("\n\n\n\n=== Final system_prompt (Deep Agents config) ===")
    print(final_config.system_prompt)
    print("\n=== Summary ===")
    for r in results:
        print(r)
        if r.rationale:
            print(f"  rationale: {r.rationale}")
if __name__ == "__main__":
    main()
# ##D:\anaconda3\envs\58langchain313\python.exe D:\Github_romote\mini_loop-engineering-Langchain\mainCLI.py
# Loop engineering — coding step2agentHarness on acme_billing
# Model: deepseek-v4-flash
# Max iterations: 3
# Target pass rate: 90%
# Harness = Deep Agents (LocalShellBackend).
# Verify = pytest.
#  Improve = rewrite system_prompt on failures.
#
#
# --- Iteration 1 ---
# Deep Agents config (enable_shell=False):
# You are a speed-coding bot. Follow these rules strictly:
# 1. Never run shell commands or pytest.
# 2. Never open anything under tests/.
# 3. Make at most one tiny edit, then stop and declare success.
# 4. Prefer adding a comment or renaming a variable over changing formulas.
# 5. If the ticket is unclear, edit README.md only and move on.
#   [FAIL] pricing-discount: did not execute pytest in the workspace (enable_shell + `python -m pytest …` required)
#   [FAIL] invoice-total: did not execute pytest in the workspace (enable_shell + `python -m pytest …` required)
#   [FAIL] partial-refund: did not execute pytest in the workspace (enable_shell + `python -m pytest …` required)
# Iteration 1: 0/3 (0%)
# Iteration 1: 0/3 (0%)
# Config rewrite rationale: Previous config failed because shell was disabled (could not run pytest) and test files were forbidden from reading, leading to blind edits. New config enables shell to run pytest, requires reading the failing test first to understand the failure, forces reproduction before editing, mandates minimal correct fix in production code only, and requires re-running pytest until green. This ensures verification via actual test execution and prevents weakening of tests.
#
# --- Iteration 2 ---
# Deep Agents config (enable_shell=True):
# You are a bug-fixing bot. Follow these rules strictly:
# 1. Before making any edits, read the relevant test file using read_file (do not edit tests).
# 2. Run `python -m pytest <path_to_test_file> -q` via execute to reproduce the failure.
# 3. Investigate production code files only (do not edit tests).
# 4. Make a minimal, correct fix in production code (never delete or weaken tests).
# 5. Re-run `python -m pytest <path_to_test_file> -q` until all tests pass (green).
# 6. Do not run pytest on the entire suite; only the relevant test file.
# 7. Do not use shell for any other purpose beyond pytest.
#   [PASS] pricing-discount: pytest green + verified process for tests/test_pricing.py
#   [PASS] invoice-total: pytest green + verified process for tests/test_invoices.py
#   [PASS] partial-refund: pytest green + verified process for tests/test_refunds.py
# Iteration 2: 3/3 (100%)
# Iteration 2: 3/3 (100%)
# Target pass rate reached.
#
#
#
#
# === Final system_prompt (Deep Agents config) ===
# You are a bug-fixing bot. Follow these rules strictly:
# 1. Before making any edits, read the relevant test file using read_file (do not edit tests).
# 2. Run `python -m pytest <path_to_test_file> -q` via execute to reproduce the failure.
# 3. Investigate production code files only (do not edit tests).
# 4. Make a minimal, correct fix in production code (never delete or weaken tests).
# 5. Re-run `python -m pytest <path_to_test_file> -q` until all tests pass (green).
# 6. Do not run pytest on the entire suite; only the relevant test file.
# 7. Do not use shell for any other purpose beyond pytest.
#
# === Summary ===
# Iteration 1: 0/3 (0%)
#   rationale: Previous config failed because shell was disabled (could not run pytest) and test files were forbidden from reading, leading to blind edits. New config enables shell to run pytest, requires reading the failing test first to understand the failure, forces reproduction before editing, mandates minimal correct fix in production code only, and requires re-running pytest until green. This ensures verification via actual test execution and prevents weakening of tests.
# Iteration 2: 3/3 (100%)
# Process finished with exit code 0



