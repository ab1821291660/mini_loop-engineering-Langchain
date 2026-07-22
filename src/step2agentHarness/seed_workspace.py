"""Load / copy the buggy acme_billing seed repo for each step2agentHarness run."""

from __future__ import annotations

import shutil
from pathlib import Path

SEED_ROOT = Path(__file__).resolve().parents[1] / "seed_repo"
# SEED_ROOT = Path(__file__).resolve().parents[1] / "seed_repo"


def load_seed_files() -> dict[str, str]:
    """path → text for UI display (relative to seed_repo)."""
    files: dict[str, str] = {}
    for path in SEED_ROOT.rglob("*"):
        if not path.is_file():
            continue
        if path.name.startswith(".") or "__pycache__" in path.parts:
            continue
        rel = path.relative_to(SEED_ROOT).as_posix()
        files[rel] = path.read_text(encoding="utf-8")
    return files
def materialize_workspace(dest: Path) -> Path:
    """Copy seed_repo into dest and return dest."""
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(
        SEED_ROOT,
        dest,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".pytest_cache"),
    )
    return dest


def read_workspace_files(root: Path) -> dict[str, str]:
    files: dict[str, str] = {}
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if path.name.startswith(".") or "__pycache__" in path.parts:
            continue
        if ".pytest_cache" in path.parts:
            continue
        rel = path.relative_to(root).as_posix()
        try:
            files[rel] = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
    return files


SEED_FILES = load_seed_files()##===================================
