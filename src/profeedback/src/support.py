# Copyright (C) 2026 AnkiCraft
# License: GNU AGPL, version 3 or later — https://www.gnu.org/licenses/agpl.html
from __future__ import annotations

import os

from aqt import mw
from aqt.qt import (
    QDesktopServices,
    QDialog,
    QDialogButtonBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPixmap,
    QPushButton,
    QSizePolicy,
    Qt,
    QTimer,
    QUrl,
    QVBoxLayout,
    QWidget,
)

from .config import is_welcome_shown, mark_welcome_shown
from .constants import (
    ADDON_DISPLAY_NAME,
    ADDON_NAME,
    ADDON_ROOT,
    ADDON_VERSION,
    ANKIWEB_ID,
    ANKIWEB_REVIEW_URL,
    COLOR_ACCENT,
    COLOR_KOFI_BG,
    COLOR_KOFI_HOVER,
    COLOR_PATREON_BG,
    COLOR_PATREON_HOVER,
    COLOR_RATE_BG,
    COLOR_RATE_HOVER,
    LOGO_FILENAME,
    LOGO_SIZE_PX,
    URL_KOFI,
    URL_PATREON,
    URL_REPORT_BUG,
    WELCOME_DELAY_MS,
)
from .i18n import ui
from .logging_utils import log_error


def _open(url: str) -> None:
    QDesktopServices.openUrl(QUrl(url))


def _colored_button(label: str, bg: str, hover: str) -> QPushButton:
    btn = QPushButton(label)
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    btn.setStyleSheet(
        f"QPushButton{{background:{bg};color:#fff;border:none;"
        f"border-radius:6px;padding:6px 14px;font-weight:600;}}"
        f"QPushButton:hover{{background:{hover};}}"
    )
    return btn


class WelcomeDialog(QDialog):
    def __init__(self) -> None:
        super().__init__(mw)
        self.setWindowTitle(ADDON_DISPLAY_NAME)
        self.setMinimumWidth(460)
        self.setMaximumWidth(520)
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # Logo
        logo_path = os.path.join(ADDON_ROOT, LOGO_FILENAME)
        if os.path.isfile(logo_path):
            try:
                pix = QPixmap(logo_path).scaled(
                    LOGO_SIZE_PX, LOGO_SIZE_PX,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                logo_lbl = QLabel()
                logo_lbl.setPixmap(pix)
                logo_lbl.setAlignment(Qt.AlignmentFlag.AlignHCenter)
                layout.addWidget(logo_lbl)
            except Exception as error:
                log_error("WelcomeDialog.logo", error)

        # Title
        title_lbl = QLabel(f"{ADDON_NAME} v{ADDON_VERSION}")
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        title_lbl.setStyleSheet(
            f"font-size:17px;font-weight:700;color:{COLOR_ACCENT};"
        )
        layout.addWidget(title_lbl)

        by_lbl = QLabel("by AnkiCraft")
        by_lbl.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        by_lbl.setStyleSheet("font-size:11px;color:gray;margin-top:-4px;")
        layout.addWidget(by_lbl)

        # Body
        body_lbl = QLabel(ui("welcome_body"))
        body_lbl.setWordWrap(True)
        body_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft)
        body_lbl.setStyleSheet("font-size:13px;margin-top:6px;")
        layout.addWidget(body_lbl)

        # AGPLv3 note
        note_lbl = QLabel(ui("welcome_support_note"))
        note_lbl.setWordWrap(True)
        note_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft)
        note_lbl.setStyleSheet("font-size:11px;color:gray;margin-top:4px;")
        layout.addWidget(note_lbl)

        # Support buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        kofi_btn = _colored_button(ui("kofi_button"), COLOR_KOFI_BG, COLOR_KOFI_HOVER)
        kofi_btn.setToolTip(ui("kofi_tooltip"))
        kofi_btn.clicked.connect(lambda: _open(URL_KOFI))

        patreon_btn = _colored_button(ui("patreon_button"), COLOR_PATREON_BG, COLOR_PATREON_HOVER)
        patreon_btn.clicked.connect(lambda: _open(URL_PATREON))

        rate_btn: QPushButton | None = None
        if ANKIWEB_ID:
            rate_btn = _colored_button(ui("rate_button"), COLOR_RATE_BG, COLOR_RATE_HOVER)
            rate_btn.clicked.connect(lambda: _open(ANKIWEB_REVIEW_URL))

        btn_row.addWidget(kofi_btn)
        btn_row.addWidget(patreon_btn)
        if rate_btn is not None:
            btn_row.addWidget(rate_btn)
        layout.addLayout(btn_row)

        # Close button
        bbox = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        close_btn = bbox.button(QDialogButtonBox.StandardButton.Close)
        if close_btn is not None:
            close_btn.setText(ui("welcome_close"))
            close_btn.setDefault(True)
            close_btn.setFocus()
        bbox.rejected.connect(self.accept)
        layout.addWidget(bbox)


def maybe_show_welcome() -> None:
    try:
        if is_welcome_shown():
            return
        mark_welcome_shown()
        QTimer.singleShot(WELCOME_DELAY_MS, _show_welcome)
    except Exception as error:
        log_error("maybe_show_welcome", error)


def _show_welcome() -> None:
    try:
        WelcomeDialog().exec()
    except Exception as error:
        log_error("_show_welcome", error)


def build_support_row(parent: QWidget) -> QFrame:
    # Gray bottom bar — no extra separator line; the background shift is the divider.
    container = QFrame(parent)
    container.setObjectName("pf-support-bar")
    container.setStyleSheet(
        "#pf-support-bar{"
        "background:transparent;"
        "border-top:1px solid rgba(255,255,255,0.08);"
        "}"
    )
    row = QHBoxLayout(container)
    row.setContentsMargins(8, 4, 8, 4)
    row.setSpacing(8)

    # Left: version · Report a bug (muted gray, same shade as Hider)
    version_label = QLabel(
        f'<span style="color:#888;font-size:11px;">'
        f'{ADDON_NAME} v{ADDON_VERSION} · '
        f'<a href="{URL_REPORT_BUG}" style="color:#888;">{ui("report_button")}</a>'
        f'</span>'
    )
    version_label.setOpenExternalLinks(True)
    version_label.setTextFormat(Qt.TextFormat.RichText)
    version_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
    row.addWidget(version_label)

    # Right: Ko-fi, Patreon, Rate — plain system buttons, no brand colors here
    kofi_btn = QPushButton(ui("kofi_button"))
    kofi_btn.setCursor(Qt.CursorShape.PointingHandCursor)
    kofi_btn.clicked.connect(lambda: _open(URL_KOFI))

    patreon_btn = QPushButton(ui("patreon_button"))
    patreon_btn.setCursor(Qt.CursorShape.PointingHandCursor)
    patreon_btn.clicked.connect(lambda: _open(URL_PATREON))

    row.addWidget(kofi_btn)
    row.addWidget(patreon_btn)

    if ANKIWEB_ID:
        rate_btn = QPushButton(ui("rate_button"))
        rate_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        rate_btn.clicked.connect(lambda: _open(ANKIWEB_REVIEW_URL))
        row.addWidget(rate_btn)

    return container
