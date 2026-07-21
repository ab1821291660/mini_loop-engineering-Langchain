"""Simple JSONL trace store for improvement-loop iterations."""

from __future__ import annotations
import json
from pathlib import Path
TRACE_PATH = Path(__file__).parent.parent / "data" / "traces.jsonl"
HARNESS_PATH = Path(__file__).parent.parent / "data" / "harness.json"
def save_harness(harness: dict) -> None:
    HARNESS_PATH.parent.mkdir(parents=True, exist_ok=True)
    HARNESS_PATH.write_text(json.dumps(harness, indent=2), encoding="utf-8")
def load_harness() -> dict | None:
    if not HARNESS_PATH.exists():
        return None
    return json.loads(HARNESS_PATH.read_text(encoding="utf-8"))




def append_traces(traces: list[dict]) -> None:
    TRACE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with TRACE_PATH.open("a", encoding="utf-8") as f:
        for trace in traces:
            f.write(json.dumps(trace, ensure_ascii=False) + "\n")

def clear_traces() -> None:
    if TRACE_PATH.exists():
        TRACE_PATH.unlink()

def load_all_traces() -> list[dict]:
    if not TRACE_PATH.exists():
        return []
    traces: list[dict] = []
    with TRACE_PATH.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                traces.append(json.loads(line))
    return traces

def get_failures(iteration: int) -> list[dict]:
    if not TRACE_PATH.exists():
        return []
    failures: list[dict] = []
    with TRACE_PATH.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            trace = json.loads(line)
            if trace.get("iteration") == iteration and trace.get("verdict") == "fail":##===================================
                failures.append(trace)
    return failures
