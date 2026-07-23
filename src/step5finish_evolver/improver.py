"""Improvement step: rewrite Deep Agents config from failing pytest traces."""

from __future__ import annotations

from pydantic import BaseModel, Field

from src.skill.harness_config import HarnessConfig
from src.llm.llm import build_chat_model
# from langchain.chat_models import init_chat_model

class ConfigPatch(BaseModel):
    system_prompt: str = Field(
        description="Full replacement system_prompt for create_deep_agent."
    )
    enable_shell: bool = Field(
        description="Whether the step2agentHarness should get LocalShellBackend (execute/pytest)."
    )
    rationale: str = Field(
        description="Which failure modes this config change targets."
    )


def propose_config(
    failures: list[dict],
    current: HarnessConfig,
    model: str | None = None,
) -> tuple[HarnessConfig, str]:
    llm = build_chat_model(model, temperature=0.2)
    # DeepSeek's thinking models reject the forced tool_choice used by
    # function-calling structured output, so use JSON mode and describe the
    # schema in the prompt instead.
    ##提示词中有体现
    structured = llm.with_structured_output(ConfigPatch, method="json_mode")##===================================
    # structured = llm.with_structured_output(ConfigPatch)##===================================

    failure_text = "\n\n".join(
        (
            f"Ticket: {t.get('task_id')}\n"
            f"Request: {t.get('request')}\n"
            f"Tools used: {t.get('tools_called')}\n"
            f"Edited: {t.get('edited_paths')}\n"
            f"Read: {t.get('read_paths')}\n"
            f"Feedback: {t.get('feedback')}\n"
            f"Pytest (tail): {(t.get('pytest_output') or '')[-800:]}\n"
            f"Hint: {t.get('failure_hint', '')}"
        )
        for t in failures
    )
    prompt = f"""You improve how a Deep Agents *coding harness* is configured.

The harness already provides planning + filesystem tools. Shell execute is a
config flag (enable_shell). You rewrite system_prompt and enable_shell.

Use case: fix bugs in a Python package. Verification is pytest. Test files
must not be edited.

Current config:
system_prompt:
{current.system_prompt}

enable_shell: {current.enable_shell}

Failing verification traces:
{failure_text}

Rewrite config so the step2agentHarness:
- enables shell (enable_shell=true) so it can run pytest
- reads the failing test file with read_file before editing
- reproduces with `python -m pytest <path> -q` via execute
- makes a minimal correct fix in production code only
- re-runs pytest until green
- never deletes or weakens tests

Verification requires ALL of: read the test, execute pytest, edit the right
module, and pytest green. A lucky code fix without that process still fails.

Return a complete replacement system_prompt (not a diff) and enable_shell.


Respond with ONLY a single JSON object (no markdown code fences) with exactly
these keys:
- "system_prompt": string — the full replacement system prompt
- "enable_shell": boolean — whether to enable the shell (execute/pytest)
- "rationale": string — which failure modes this config change targets"""


    patch: ConfigPatch = structured.invoke(prompt)##===================================
    improved = HarnessConfig(
        system_prompt=patch.system_prompt.strip(),
        enable_shell=patch.enable_shell,
    )
    return improved, patch.rationale.strip()

