from __future__ import annotations

import base64
import os
from typing import Final

from aqt import mw

from .logging_utils import log_error


class FontLoader:
    __slots__ = ("_addon_dir", "_css_cache")

    _FONT_NAMES: Final[tuple[str, ...]] = ("Feather Bold.ttf",)

    def __init__(self, addon_dir: str) -> None:
        self._addon_dir: str = addon_dir
        self._css_cache: str | None = None

    def font_face_css(self) -> str:
        if self._css_cache is not None:
            return self._css_cache

        roots: list[str] = [
            os.path.join(self._addon_dir, "user_files"),
            self._addon_dir,
        ]
        candidates: list[str] = [
            os.path.join(root, name) for root in roots for name in self._FONT_NAMES
        ]
        try:
            media_dir = mw.col.media.dir()
            candidates += [os.path.join(media_dir, name) for name in self._FONT_NAMES]
        except Exception as error:
            log_error("FontLoader.media_dir", error)

        for path in candidates:
            if not os.path.isfile(path):
                continue
            try:
                with open(path, "rb") as handle:
                    encoded = base64.b64encode(handle.read()).decode("ascii")
                self._css_cache = (
                    "@font-face{font-family:'Feather';"
                    f"src:url('data:font/truetype;base64,{encoded}') format('truetype');"
                    "font-weight:bold;font-style:normal;font-display:block}"
                )
                return self._css_cache
            except OSError as error:
                log_error(f"FontLoader.read[{path}]", error)

        self._css_cache = ""
        return ""
