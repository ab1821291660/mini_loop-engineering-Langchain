"""CLI entry for the Deep Agents + loop engineering demo."""
import os
from dotenv import load_dotenv
from src.harness_config import INITIAL_CONFIG
from src.loop import run_improvement_loop##===================================
from src.trace_store import clear_traces##===================================
def main() -> None:
    load_dotenv()

    model = os.getenv("AGENT_MODEL", "openai:gpt-4.1-mini")
    max_iterations = int(os.getenv("MAX_ITERATIONS", "3"))
    target_pass_rate = float(os.getenv("TARGET_PASS_RATE", "0.9"))
    reset = os.getenv("RESET_TRACES", "1") == "1"
    if reset:
        clear_traces()
    print("Loop engineering — coding agent on acme_billing")
    print(f"Model: {model}")
    print(f"Max iterations: {max_iterations}")
    print(f"Target pass rate: {target_pass_rate:.0%}")
    print("\nHarness = Deep Agents (LocalShellBackend).")##===================================
    print("Verify = pytest. "##===================================
          "Improve = rewrite system_prompt on failures.\n")##===================================


    results, final_config = run_improvement_loop(
        initial_config=INITIAL_CONFIG,
        model=model,
        max_iterations=max_iterations,
        target_pass_rate=target_pass_rate,
    )
    print("\n=== Final system_prompt (Deep Agents config) ===")
    print(final_config.system_prompt)
    print("\n=== Summary ===")
    for r in results:
        print(r)
        if r.rationale:
            print(f"  rationale: {r.rationale}")
if __name__ == "__main__":
    main()

