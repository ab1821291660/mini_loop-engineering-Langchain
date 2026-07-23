"""Smoke-test the improve_loop graph on the local Agent Server."""
import asyncio
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from langgraph_sdk import get_client
async def main() -> None:
    client = get_client(url="http://localhost:2025")##===================================
    print("Invoking Studio graph: improve_loop")
    final = None
    async for chunk in client.runs.stream(
        None,
        "improve_loop",
        input={"max_iterations": 2, "target_pass_rate": 0.9},
        stream_mode="values",
    ):
        if chunk.event == "values":
            final = chunk.data
            print(
                f"  iter={final.get('iteration')} "
                f"pass_rate={final.get('pass_rate')} "
                f"status={final.get('status')}"
            )


    if final:
        print(json.dumps({
            "stop_reason": final.get("stop_reason"),
            "system_prompt": final.get("system_prompt"),
            "enable_shell": final.get("enable_shell"),
        }, indent=2)[:1500])
if __name__ == "__main__":
    asyncio.run(main())

