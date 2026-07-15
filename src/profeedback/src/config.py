from __future__ import annotations

from dataclasses import asdict, dataclass, fields

from aqt import mw

from .constants import PACKAGE
from .logging_utils import log_error


@dataclass(slots=True, frozen=True)
class AddonConfig:
    answerSoundEnabled: bool = True
    sessionSoundsEnabled: bool = True
    confettiEnabled: bool = True
    styledButtonsEnabled: bool = True
    flagsEnabled: bool = True
    answerSound: str = ""
    deckFinishSound: str = ""
    allDoneSound: str = ""
    deckPerfectSound: str = ""
    allPerfectSound: str = ""

    @classmethod
    def load(cls) -> "AddonConfig":
        try:
            raw = mw.addonManager.getConfig(PACKAGE) or {}
            # Migration: configs written before the brand-neutral rename.
            if "styledButtonsEnabled" not in raw and "duolingoButtonsEnabled" in raw:
                raw["styledButtonsEnabled"] = raw["duolingoButtonsEnabled"]
            known = {field.name for field in fields(cls)}
            data = {key: value for key, value in raw.items() if key in known}
            return cls(**data)
        except Exception as error:
            log_error("AddonConfig.load", error)
            return cls()

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def save_config(config: AddonConfig) -> None:
    try:
        # Merge so internal keys (e.g. confetti day state) survive a settings save.
        raw = mw.addonManager.getConfig(PACKAGE) or {}
        raw.update(config.to_dict())
        mw.addonManager.writeConfig(PACKAGE, raw)
    except Exception as error:
        log_error("save_config", error)


@dataclass(slots=True)
class DayState:
    date: str = ""
    answers: int = 0
    perfect: bool = True


def load_day_state() -> DayState:
    try:
        raw = mw.addonManager.getConfig(PACKAGE) or {}
        date = raw.get("confettiDayDate")
        answers = raw.get("confettiDayAnswers")
        perfect = raw.get("confettiDayPerfect")
        return DayState(
            date=date if isinstance(date, str) else "",
            answers=answers if isinstance(answers, int) and answers >= 0 else 0,
            perfect=perfect if isinstance(perfect, bool) else True,
        )
    except Exception as error:
        log_error("load_day_state", error)
        return DayState()


def save_day_state(state: DayState) -> None:
    try:
        raw = mw.addonManager.getConfig(PACKAGE) or {}
        raw["confettiDayDate"] = state.date
        raw["confettiDayAnswers"] = state.answers
        raw["confettiDayPerfect"] = state.perfect
        mw.addonManager.writeConfig(PACKAGE, raw)
    except Exception as error:
        log_error("save_day_state", error)


def is_welcome_shown() -> bool:
    try:
        raw = mw.addonManager.getConfig(PACKAGE) or {}
        meta = raw.get("_meta")
        if isinstance(meta, dict):
            return bool(meta.get("welcome_shown", False))
        return False
    except Exception as error:
        log_error("is_welcome_shown", error)
        return True


def mark_welcome_shown() -> None:
    try:
        raw = mw.addonManager.getConfig(PACKAGE) or {}
        if not isinstance(raw.get("_meta"), dict):
            raw["_meta"] = {}
        raw["_meta"]["welcome_shown"] = True
        mw.addonManager.writeConfig(PACKAGE, raw)
    except Exception as error:
        log_error("mark_welcome_shown", error)
