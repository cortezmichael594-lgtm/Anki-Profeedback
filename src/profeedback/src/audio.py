from __future__ import annotations

import os
import random

from aqt import mw

from .logging_utils import log_error


class _Channel:
    __slots__ = ("player", "output", "loaded_path", "fixed_name")

    def __init__(self, player: object, output: object) -> None:
        self.player: object = player
        self.output: object = output
        self.loaded_path: str = ""
        self.fixed_name: str = ""


_channels: dict[str, _Channel] = {}


def _mp3_paths(folder: str) -> list[str]:
    try:
        return [
            os.path.join(folder, name)
            for name in os.listdir(folder)
            if name.lower().endswith(".mp3")
        ]
    except OSError:
        return []


def list_sound_names(folder: str) -> list[str]:
    try:
        return sorted(
            name for name in os.listdir(folder) if name.lower().endswith(".mp3")
        )
    except OSError:
        return []


def has_sounds(folder: str) -> bool:
    return bool(_mp3_paths(folder))


def _ensure_channel(folder: str) -> _Channel | None:
    channel = _channels.get(folder)
    if channel is not None:
        return channel
    try:
        from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer

        player = QMediaPlayer(mw)
        output = QAudioOutput(mw)
        player.setAudioOutput(output)
        output.setVolume(1.0)
        channel = _Channel(player, output)
        _channels[folder] = channel
        # After a random file finishes, pre-decode a different one so the next
        # play starts instantly and still varies.
        player.mediaStatusChanged.connect(
            lambda status, f=folder: _on_media_status(f, status)
        )
        return channel
    except Exception as error:
        log_error("audio._ensure_channel", error)
        return None


def _pick_path(folder: str, filename: str) -> str:
    if filename:
        path = os.path.join(folder, filename)
        if os.path.isfile(path):
            return path
    paths = _mp3_paths(folder)
    return random.choice(paths) if paths else ""


def _set_source(channel: _Channel, path: str) -> None:
    from PyQt6.QtCore import QUrl

    channel.player.setSource(QUrl.fromLocalFile(path))  # type: ignore[attr-defined]
    channel.loaded_path = path


def preload(folder: str, filename: str = "") -> None:
    # Decoding an mp3 the first time is the expensive part; doing it here, far
    # from any click, is what keeps playback latency near zero later.
    try:
        channel = _ensure_channel(folder)
        if channel is None:
            return
        channel.fixed_name = filename if filename else ""
        path = _pick_path(folder, filename)
        if path and channel.loaded_path != path:
            _set_source(channel, path)
    except Exception as error:
        log_error("audio.preload", error)


def play_named(folder: str, filename: str) -> None:
    try:
        channel = _ensure_channel(folder)
        if channel is None:
            return
        channel.fixed_name = filename if filename else ""
        named_path = os.path.join(folder, filename) if filename else ""
        use_loaded = bool(channel.loaded_path) and (
            channel.loaded_path == named_path
            or (not filename and os.path.dirname(channel.loaded_path) == folder)
        )
        if use_loaded:
            channel.player.setPosition(0)  # type: ignore[attr-defined]
            channel.player.play()  # type: ignore[attr-defined]
            return
        path = _pick_path(folder, filename)
        if not path:
            return
        _set_source(channel, path)
        channel.player.play()  # type: ignore[attr-defined]
    except Exception as error:
        log_error("audio.play_named", error)


def play_from(folder: str) -> None:
    play_named(folder, "")


def _on_media_status(folder: str, status: object) -> None:
    try:
        from PyQt6.QtMultimedia import QMediaPlayer

        if status != QMediaPlayer.MediaStatus.EndOfMedia:
            return
        channel = _channels.get(folder)
        if channel is None or channel.fixed_name:
            return
        paths = _mp3_paths(folder)
        if len(paths) < 2:
            return
        options = [p for p in paths if p != channel.loaded_path]
        _set_source(channel, random.choice(options))
    except Exception as error:
        log_error("audio._on_media_status", error)


def dispose_players() -> None:
    for channel in list(_channels.values()):
        try:
            channel.player.stop()  # type: ignore[attr-defined]
        except Exception as error:
            log_error("audio.dispose_players", error)
    _channels.clear()