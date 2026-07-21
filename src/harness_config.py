"""Improvable knobs on top of the Deep Agents coding harness.

Deep Agents is the harness. These fields are what the improvement loop rewrites
when pytest fails — deliberately weak at the start so iteration 1 fails.
"""

from __future__ import annotations

from copy import deepcopy

from pydantic import BaseModel, Field


class HarnessConfig(BaseModel):
    system_prompt: str = Field(
        description="Instructions passed into create_deep_agent(system_prompt=...)."
    )
    enable_shell: bool = Field(
        default=False,
        description="If True, LocalShellBackend (execute/pytest). If False, filesystem only.",
    )

    def snapshot(self) -> dict:
        return self.model_dump()


# Deliberately weak — no shell, bad process — so iteration 1 fails and the loop improves.
INITIAL_CONFIG = HarnessConfig(
    system_prompt=(
        "You are a speed-coding bot. Follow these rules strictly:\n"
        "1. Never run shell commands or pytest.\n"
        "2. Never open anything under tests/.\n"
        "3. Make at most one tiny edit, then stop and declare success.\n"
        "4. Prefer adding a comment or renaming a variable over changing formulas.\n"
        "5. If the ticket is unclear, edit README.md only and move on."
    ),
    enable_shell=False,
)


def clone_config(config: HarnessConfig) -> HarnessConfig:
    return HarnessConfig.model_validate(deepcopy(config.model_dump()))
