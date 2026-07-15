from __future__ import annotations

import os
from typing import Final

PACKAGE: Final[str] = __name__.split(".")[0]
ADDON_ROOT: Final[str] = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
USER_FILES_DIR: Final[str] = os.path.join(ADDON_ROOT, "user_files")


def _data_root() -> str:
    # user_files/ survives addon reinstalls; prefer it when the sounds live there.
    if os.path.isdir(os.path.join(USER_FILES_DIR, "sonidos")):
        return USER_FILES_DIR
    return ADDON_ROOT


SONIDOS_DIR: Final[str] = os.path.join(_data_root(), "sonidos")
CORRECTO_DIR: Final[str] = os.path.join(SONIDOS_DIR, "correcto")
FINALIZADO_DIR: Final[str] = os.path.join(SONIDOS_DIR, "finalizado")
FIN_MAZO_DIR: Final[str] = os.path.join(FINALIZADO_DIR, "mazo")
FIN_TODO_DIR: Final[str] = os.path.join(FINALIZADO_DIR, "todo")
PERFECTO_MAZO_DIR: Final[str] = os.path.join(SONIDOS_DIR, "perfecto-mazo")
PERFECTO_TODO_DIR: Final[str] = os.path.join(SONIDOS_DIR, "perfecto-todo")
WEB_DIR: Final[str] = os.path.join(ADDON_ROOT, "web")
WEB_EXPORT_PATTERN: Final[str] = r"web[/\\].*\.(css|js|ttf|woff2?)$"

DECK_CONFETTI_MIN_ANSWERS: Final[int] = 5
ALL_DONE_CONFETTI_MIN_ANSWERS: Final[int] = 20

# ── AnkiCraft branding ────────────────────────────────────────────────────────
ADDON_NAME: Final[str] = "ProFeedback"
ADDON_DISPLAY_NAME: Final[str] = "ProFeedback (by AnkiCraft)"
ADDON_VERSION: Final[str] = "1.0.0"
AUTHOR_NAME: Final[str] = "AnkiCraft"
ANKIWEB_ID: Final[str] = "392368329"
ANKIWEB_PAGE_URL: Final[str] = f"https://ankiweb.net/shared/info/{ANKIWEB_ID}"
ANKIWEB_REVIEW_URL: Final[str] = f"https://ankiweb.net/shared/review/{ANKIWEB_ID}"
URL_KOFI: Final[str] = "https://ko-fi.com/ankicraft"
URL_PATREON: Final[str] = "https://www.patreon.com/cw/Ankicraft594"
URL_REPORT_BUG: Final[str] = ANKIWEB_PAGE_URL
LOGO_FILENAME: Final[str] = "logo.png"
LOGO_SIZE_PX: Final[int] = 72
COLOR_ACCENT: Final[str] = "#7C5CE0"
COLOR_KOFI_BG: Final[str] = "#29ABE0"
COLOR_KOFI_HOVER: Final[str] = "#1E8FBF"
COLOR_PATREON_BG: Final[str] = "#FF424D"
COLOR_PATREON_HOVER: Final[str] = "#E0313C"
COLOR_RATE_BG: Final[str] = "#F5A623"
COLOR_RATE_HOVER: Final[str] = "#D98E12"
CONFIG_KEY_META: Final[str] = "_meta"
META_KEY_WELCOME_SHOWN: Final[str] = "welcome_shown"
WELCOME_DELAY_MS: Final[int] = 2000
