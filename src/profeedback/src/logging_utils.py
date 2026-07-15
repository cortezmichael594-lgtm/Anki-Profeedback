from __future__ import annotations

from .constants import PACKAGE


def log_error(context: str, detail: object) -> None:
    print(f"[{PACKAGE}] {context}: {detail}")
