from __future__ import annotations

from urllib.parse import quote

from aqt import mw

from .constants import PACKAGE, WEB_EXPORT_PATTERN
from .logging_utils import log_error

_WEB_BASE: str = f"/_addons/{quote(PACKAGE)}/web/"


def register_web_exports() -> None:
    try:
        mw.addonManager.setWebExports(PACKAGE, WEB_EXPORT_PATTERN)
    except Exception as error:
        log_error("register_web_exports", error)


def stylesheet_tag(filename: str) -> str:
    return f'<link rel="stylesheet" href="{_WEB_BASE}{filename}">'


def script_tag(filename: str) -> str:
    return f'<script src="{_WEB_BASE}{filename}" defer></script>'


def inline_style(css: str) -> str:
    return f"<style>{css}</style>" if css else ""
