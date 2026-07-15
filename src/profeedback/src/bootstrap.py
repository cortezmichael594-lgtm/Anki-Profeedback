from __future__ import annotations

from aqt import gui_hooks, mw

from .constants import PACKAGE
from .controller import FeedbackController
from .logging_utils import log_error

_controller: FeedbackController | None = None


def setup() -> None:
    global _controller
    try:
        gui_hooks.main_window_did_init.append(_maybe_show_welcome)
    except Exception as error:
        log_error("setup.welcome_hook", error)
    try:
        _controller = FeedbackController()
    except Exception as error:
        log_error("setup", error)
        return
    try:
        mw.addonManager.setConfigAction(PACKAGE, _open_config_dialog)
    except Exception as error:
        log_error("setConfigAction", error)
    if hasattr(gui_hooks, "main_window_will_close"):
        gui_hooks.main_window_will_close.append(_on_main_window_will_close)


def _maybe_show_welcome() -> None:
    from .support import maybe_show_welcome
    maybe_show_welcome()


def _open_config_dialog() -> None:
    from .config_dialog import show_config_dialog

    show_config_dialog(on_saved=_reload_controller)


def _reload_controller() -> None:
    if _controller is not None:
        _controller.reload()


def _on_main_window_will_close() -> None:
    global _controller
    try:
        if _controller is not None:
            _controller.cleanup()
    except Exception as error:
        log_error("_on_main_window_will_close", error)
    finally:
        _controller = None
