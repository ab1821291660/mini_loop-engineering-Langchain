"""Windows UTF-8 subprocess shim.

On Chinese/CJK Windows the default locale encoding is GBK (cp936). deepagents'
``LocalShellBackend`` runs shell commands via ``subprocess.run(..., text=True)``
without an explicit ``encoding``, so it decodes child output (e.g. ``pytest``)
using GBK. When that output contains non-GBK bytes (``–``, ``→``, ``≥`` and
similar UTF-8 characters), the subprocess reader thread raises
``UnicodeDecodeError`` and crashes the run — but only once the improvement loop
enables the shell (``enable_shell=True``), since iteration 1 never spawns a
shell.

This shim, applied on import, makes the fix transparent for every entry point
(CLI, Web, Studio):

- child Python processes emit UTF-8 (``PYTHONUTF8`` / ``PYTHONIOENCODING``);
- ``subprocess.run`` in text mode decodes as UTF-8 with ``errors="replace"``.
"""

from __future__ import annotations

import os
import subprocess

_APPLIED = False


def apply() -> None:
    """Install the UTF-8 subprocess shim (idempotent, Windows-only)."""
    global _APPLIED
    if _APPLIED:
        return
    _APPLIED = True
    if os.name != "nt":
        return

    # Make child Python processes (e.g. `python -m pytest`) emit UTF-8.
    os.environ.setdefault("PYTHONUTF8", "1")
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")

    _orig_run = subprocess.run

    def _run(*args, **kwargs):
        # Only touch text-mode captures that don't already pin an encoding —
        # exactly how LocalShellBackend calls subprocess.run.
        if (kwargs.get("text") or kwargs.get("universal_newlines")) and not kwargs.get(
            "encoding"
        ):
            kwargs["encoding"] = "utf-8"
            kwargs.setdefault("errors", "replace")
        return _orig_run(*args, **kwargs)

    subprocess.run = _run  # type: ignore[assignment]


apply()
