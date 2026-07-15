from __future__ import annotations

from collections.abc import Callable

from aqt import mw
from aqt.qt import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

from .audio import list_sound_names, play_named
from .config import AddonConfig, save_config
from .constants import (
    CORRECTO_DIR,
    FIN_MAZO_DIR,
    FIN_TODO_DIR,
    PERFECTO_MAZO_DIR,
    PERFECTO_TODO_DIR,
)
from .constants import ADDON_DISPLAY_NAME
from .i18n import ui
from .support import build_support_row
from .logging_utils import log_error


class ConfigDialog(QDialog):
    def __init__(self, on_saved: Callable[[], None]) -> None:
        super().__init__(mw)
        self._on_saved = on_saved
        self._config = AddonConfig.load()
        self._answer_names: list[str] = list_sound_names(CORRECTO_DIR)
        self._deck_names: list[str] = list_sound_names(FIN_MAZO_DIR)
        self._all_names: list[str] = list_sound_names(FIN_TODO_DIR)
        self._deck_perfect_names: list[str] = list_sound_names(PERFECTO_MAZO_DIR)
        self._all_perfect_names: list[str] = list_sound_names(PERFECTO_TODO_DIR)
        self._build_ui()
        self._load_values()
        self._sync_enabled()

    def _sound_row(
        self, names: list[str], handler: Callable[[], None]
    ) -> tuple[QHBoxLayout, QComboBox, QPushButton]:
        row = QHBoxLayout()
        combo = QComboBox()
        for name in names:
            combo.addItem(name, name)
        row.addWidget(combo, stretch=1)
        button = QPushButton(ui("test"))
        button.clicked.connect(handler)
        row.addWidget(button)
        return row, combo, button

    def _build_ui(self) -> None:
        self.setWindowTitle(ADDON_DISPLAY_NAME)
        self.setMinimumWidth(460)
        layout = QVBoxLayout(self)

        answer_group = QGroupBox(ui("group_answer_sounds"))
        answer_layout = QVBoxLayout(answer_group)
        self.answer_enabled = QCheckBox(ui("enable_answer_sound"))
        self.answer_enabled.toggled.connect(self._sync_enabled)
        answer_layout.addWidget(self.answer_enabled)
        if not self._answer_names:
            answer_layout.addWidget(QLabel(ui("no_answer_sounds")))
        answer_row, self.answer_combo, self.answer_test_btn = self._sound_row(
            self._answer_names, self._on_test_answer
        )
        answer_layout.addLayout(answer_row)
        layout.addWidget(answer_group)

        finish_group = QGroupBox(ui("group_finish_sounds"))
        finish_layout = QVBoxLayout(finish_group)
        self.finish_enabled = QCheckBox(ui("enable_finish_sound"))
        self.finish_enabled.toggled.connect(self._sync_enabled)
        finish_layout.addWidget(self.finish_enabled)
        if not (self._deck_names and self._all_names):
            finish_layout.addWidget(QLabel(ui("no_finish_sounds")))

        finish_layout.addWidget(QLabel(ui("label_deck_finish")))
        deck_row, self.deck_combo, self.deck_test_btn = self._sound_row(
            self._deck_names, self._on_test_deck
        )
        finish_layout.addLayout(deck_row)

        finish_layout.addWidget(QLabel(ui("label_all_done")))
        all_row, self.all_combo, self.all_test_btn = self._sound_row(
            self._all_names, self._on_test_all
        )
        finish_layout.addLayout(all_row)

        finish_layout.addWidget(QLabel(ui("label_deck_perfect")))
        deck_perfect_row, self.deck_perfect_combo, self.deck_perfect_test_btn = (
            self._sound_row(self._deck_perfect_names, self._on_test_deck_perfect)
        )
        finish_layout.addLayout(deck_perfect_row)

        finish_layout.addWidget(QLabel(ui("label_all_perfect")))
        all_perfect_row, self.all_perfect_combo, self.all_perfect_test_btn = (
            self._sound_row(self._all_perfect_names, self._on_test_all_perfect)
        )
        finish_layout.addLayout(all_perfect_row)
        layout.addWidget(finish_group)

        appearance_group = QGroupBox(ui("group_appearance"))
        appearance_layout = QVBoxLayout(appearance_group)
        self.confetti = QCheckBox(ui("confetti_option"))
        self.styled_buttons = QCheckBox(ui("styled_buttons"))
        self.flags = QCheckBox(ui("flags_option"))
        appearance_layout.addWidget(self.confetti)
        appearance_layout.addWidget(self.styled_buttons)
        appearance_layout.addWidget(self.flags)
        layout.addWidget(appearance_group)

        layout.addWidget(build_support_row(self))

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        save_button = buttons.button(QDialogButtonBox.StandardButton.Save)
        if save_button is not None:
            save_button.setText(ui("btn_accept"))
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    @staticmethod
    def _select(combo: QComboBox, value: str) -> None:
        index = combo.findData(value)
        if index >= 0:
            combo.setCurrentIndex(index)

    @staticmethod
    def _current(combo: QComboBox) -> str:
        value = combo.currentData()
        return value if isinstance(value, str) else ""

    def _load_values(self) -> None:
        config = self._config
        self.answer_enabled.setChecked(config.answerSoundEnabled)
        self.finish_enabled.setChecked(config.sessionSoundsEnabled)
        self.confetti.setChecked(config.confettiEnabled)
        self.styled_buttons.setChecked(config.styledButtonsEnabled)
        self.flags.setChecked(config.flagsEnabled)
        self._select(self.answer_combo, config.answerSound)
        self._select(self.deck_combo, config.deckFinishSound)
        self._select(self.all_combo, config.allDoneSound)
        self._select(self.deck_perfect_combo, config.deckPerfectSound)
        self._select(self.all_perfect_combo, config.allPerfectSound)

    def _sync_enabled(self) -> None:
        answer_on = self.answer_enabled.isChecked() and bool(self._answer_names)
        self.answer_combo.setEnabled(answer_on)
        self.answer_test_btn.setEnabled(answer_on)

        finish_on = self.finish_enabled.isChecked()
        deck_on = finish_on and bool(self._deck_names)
        self.deck_combo.setEnabled(deck_on)
        self.deck_test_btn.setEnabled(deck_on)

        all_on = finish_on and bool(self._all_names)
        self.all_combo.setEnabled(all_on)
        self.all_test_btn.setEnabled(all_on)

        deck_perfect_on = finish_on and bool(self._deck_perfect_names)
        self.deck_perfect_combo.setEnabled(deck_perfect_on)
        self.deck_perfect_test_btn.setEnabled(deck_perfect_on)

        all_perfect_on = finish_on and bool(self._all_perfect_names)
        self.all_perfect_combo.setEnabled(all_perfect_on)
        self.all_perfect_test_btn.setEnabled(all_perfect_on)

    def _on_test_answer(self) -> None:
        play_named(CORRECTO_DIR, self._current(self.answer_combo))

    def _on_test_deck(self) -> None:
        play_named(FIN_MAZO_DIR, self._current(self.deck_combo))

    def _on_test_all(self) -> None:
        play_named(FIN_TODO_DIR, self._current(self.all_combo))

    def _on_test_deck_perfect(self) -> None:
        play_named(PERFECTO_MAZO_DIR, self._current(self.deck_perfect_combo))

    def _on_test_all_perfect(self) -> None:
        play_named(PERFECTO_TODO_DIR, self._current(self.all_perfect_combo))

    def _collect(self) -> AddonConfig:
        return AddonConfig(
            answerSoundEnabled=self.answer_enabled.isChecked(),
            sessionSoundsEnabled=self.finish_enabled.isChecked(),
            confettiEnabled=self.confetti.isChecked(),
            styledButtonsEnabled=self.styled_buttons.isChecked(),
            flagsEnabled=self.flags.isChecked(),
            answerSound=self._current(self.answer_combo),
            deckFinishSound=self._current(self.deck_combo),
            allDoneSound=self._current(self.all_combo),
            deckPerfectSound=self._current(self.deck_perfect_combo),
            allPerfectSound=self._current(self.all_perfect_combo),
        )

    def _on_accept(self) -> None:
        try:
            save_config(self._collect())
            self._on_saved()
        except Exception as error:
            log_error("ConfigDialog._on_accept", error)
        self.accept()


def show_config_dialog(on_saved: Callable[[], None]) -> None:
    try:
        ConfigDialog(on_saved).exec()
    except Exception as error:
        log_error("show_config_dialog", error)