from __future__ import annotations

import os

from anki.cards import Card
from aqt import gui_hooks, mw
from aqt.browser.previewer import Previewer
from aqt.clayout import CardLayout
from aqt.reviewer import Reviewer, ReviewerBottomBar
from aqt.webview import WebContent

from .assets import inline_style, register_web_exports, script_tag, stylesheet_tag
from .audio import dispose_players, play_named, preload
from .config import AddonConfig
from .confetti import ConfettiManager
from .constants import (
    CORRECTO_DIR,
    FIN_MAZO_DIR,
    FIN_TODO_DIR,
    PERFECTO_MAZO_DIR,
    PERFECTO_TODO_DIR,
)
from .flags import FlagRenderer
from .fonts import FontLoader
from .logging_utils import log_error
from .review_data import clear_history_cache

_CORRECT_EASES: frozenset[int] = frozenset({3, 4})


class FeedbackController:
    __slots__ = (
        "_addon_dir",
        "_font_loader",
        "_flag_renderer",
        "_confetti_manager",
        "_config",
    )

    def __init__(self) -> None:
        self._addon_dir: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self._font_loader: FontLoader = FontLoader(self._addon_dir)
        self._flag_renderer: FlagRenderer = FlagRenderer()
        self._config: AddonConfig = AddonConfig.load()
        self._confetti_manager: ConfettiManager = ConfettiManager(lambda: self._config)
        register_web_exports()
        self._register_hooks()
        self._preload_sounds()

    @property
    def config(self) -> AddonConfig:
        return self._config

    def _preload_sounds(self) -> None:
        config = self._config
        preload(CORRECTO_DIR, config.answerSound)
        preload(FIN_MAZO_DIR, config.deckFinishSound)
        preload(FIN_TODO_DIR, config.allDoneSound)
        preload(PERFECTO_MAZO_DIR, config.deckPerfectSound)
        preload(PERFECTO_TODO_DIR, config.allPerfectSound)

    def _register_hooks(self) -> None:
        gui_hooks.webview_will_set_content.append(self._on_webview_set_content)
        gui_hooks.reviewer_did_answer_card.append(self._on_did_answer)
        gui_hooks.card_will_show.append(self._on_card_will_show)
        self._confetti_manager.register()

    def _deregister_hooks(self) -> None:
        for hook, handler in (
            (gui_hooks.webview_will_set_content, self._on_webview_set_content),
            (gui_hooks.reviewer_did_answer_card, self._on_did_answer),
            (gui_hooks.card_will_show, self._on_card_will_show),
        ):
            try:
                hook.remove(handler)
            except ValueError:
                pass
        self._confetti_manager.unregister()

    def _on_did_answer(self, reviewer: Reviewer, card: Card, ease: int) -> None:
        try:
            correct = ease in _CORRECT_EASES
            self._confetti_manager.record_answer(correct)
            config = self.config
            if config.answerSoundEnabled and correct:
                play_named(CORRECTO_DIR, config.answerSound)
        except Exception as error:
            log_error("_on_did_answer", error)

    def _on_webview_set_content(self, web_content: WebContent, context: object) -> None:
        try:
            config = self.config
            if isinstance(context, (Reviewer, CardLayout, Previewer)):
                web_content.head += inline_style(self._font_loader.font_face_css())
                if config.flagsEnabled:
                    web_content.head += stylesheet_tag("flags.css")
            if isinstance(context, ReviewerBottomBar) and config.styledButtonsEnabled:
                web_content.head += inline_style(self._font_loader.font_face_css())
                web_content.head += stylesheet_tag("buttons.css")
                web_content.body += script_tag("buttons.js")
        except Exception as error:
            log_error("_on_webview_set_content", error)

    def _on_card_will_show(self, html: str, card: Card, context: str) -> str:
        if context not in ("reviewQuestion", "reviewAnswer"):
            return html
        try:
            if not self.config.flagsEnabled:
                return html
            flag_html = self._flag_renderer.get(card)
            if flag_html and flag_html not in html:
                return flag_html + html
        except Exception as error:
            log_error("_on_card_will_show", error)
        return html

    def reload(self) -> None:
        self._config = AddonConfig.load()
        self._preload_sounds()
        self._flag_renderer.clear()
        clear_history_cache()

    def cleanup(self) -> None:
        self._deregister_hooks()
        clear_history_cache()
        self._flag_renderer.clear()
        self._confetti_manager.reset()
        dispose_players()