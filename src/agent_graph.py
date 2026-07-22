"""Deep Agents as a coding harness over a real (buggy) Python package.

Harness = create_deep_agent + filesystem/shell backend.
Config = system_prompt + enable_shell (what the improvement loop rewrites).
Verify = pytest.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend, LocalShellBackend
from dotenv import load_dotenv

from src.harness_config import INITIAL_CONFIG, HarnessConfig
from src.llm import build_chat_model

load_dotenv()

DEEP_AGENT_HARNESS = {
    "name": "Deep Agents",
    "package": "deepagents",
    "factory": "create_deep_agent",
    "backend": "LocalShellBackend | FilesystemBackend",
    "docs": "https://docs.langchain.com/oss/python/deepagents/overview",
    "use_case": (
        "Coding agent: fix bugs in acme_billing. "
        "Config toggles shell (pytest) + system_prompt; verification is pytest."
    ),
    "capabilities": [
        {
            "id": "planning",
            "title": "Planning",
            "detail": "TodoListMiddleware — write_todos for multi-step fixes",
        },
        {
            "id": "filesystem",
            "title": "Filesystem",
            "detail": "ls / read_file / write_file / edit_file / glob / grep on the repo",
        },
        {
            "id": "shell",
            "title": "Shell execute (config)",
            "detail": "enable_shell=True → LocalShellBackend so the agent can run pytest",
        },
        {
            "id": "subagents",
            "title": "Subagents",
            "detail": "task tool available; keep these tickets in-process",
        },
    ],
    "filesystem_tools": [
        "ls",
        "read_file",
        "write_file",
        "edit_file",
        "glob",
        "grep",
        "execute",
    ],
}


def make_agent(
    workspace: Path,
    config: HarnessConfig | None = None,
    model: str | None = None,
):
    """Build Deep Agents pointed at a concrete workspace directory."""
    config = config or INITIAL_CONFIG
    chat_model = build_chat_model(model)
    if config.enable_shell:
        backend = LocalShellBackend(##===================================
            root_dir=str(workspace),##===================================
            virtual_mode=True,##===================================
            inherit_env=True,
            timeout=90,
        )
        backend_note = (
            "Shell execute is enabled. You may run: python -m pytest <path> -q"
        )
    else:
        backend = FilesystemBackend(
            root_dir=str(workspace),##===================================
            virtual_mode=True,##===================================
        )
        backend_note = (
            "Shell execute is DISABLED for this run. You only have filesystem tools."
        )


    # Neutral workspace facts only — do NOT override the improvable system_prompt.
    system_prompt = (
        f"{config.system_prompt.strip()}\n\n"
        f"Workspace: acme_billing Python package (acme_billing/, tests/).\n"
        f"{backend_note}\n"
        "Do not spawn subagents — do the work yourself."
    )
    return create_deep_agent(
        #model=model, #model or os.getenv("AGENT_MODEL", "openai:gpt-4.1-mini")
        model=chat_model,
        system_prompt=system_prompt,
        backend=backend,
    )


def tools_from_messages(messages: list) -> list[str]:
    names: list[str] = []
    for msg in messages or []:
        for call in getattr(msg, "tool_calls", None) or []:
            name = call.get("name") if isinstance(call, dict) else getattr(call, "name", None)
            if name and name not in names:
                names.append(name)
    return names
def final_text(messages: list) -> str:
    if not messages:
        return ""
    content = getattr(messages[-1], "content", messages[-1])
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(block.get("text", ""))
            else:
                parts.append(str(block))
        return "\n".join(parts)
    return content if isinstance(content, str) else str(content)


def _studio_coding_agent():
    import tempfile
    from src.seed_workspace import materialize_workspace

    tmp = Path(tempfile.mkdtemp(prefix="deepagent_studio_"))
    materialize_workspace(tmp)##===================================
    return make_agent(tmp, ##===================================##===================================
                      INITIAL_CONFIG)
graph = _studio_coding_agent()
