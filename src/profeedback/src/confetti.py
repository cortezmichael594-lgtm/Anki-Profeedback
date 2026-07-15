from __future__ import annotations

import datetime
import json
from collections.abc import Callable
from dataclasses import dataclass
from typing import Final

from anki.collection import Collection
from aqt import gui_hooks, mw
from aqt.operations import QueryOp
from aqt.overview import Overview

from .config import AddonConfig, DayState, load_day_state, save_day_state
from .logging_utils import log_error

# ── Confetti colours (ProFeedback palette) ────────────────────────────────────
NORMAL_COLORS: Final[list[str]] = [
    "#ff4b4b", "#ffab33", "#93d333", "#49c0f8", "#ce82ff", "#1899d6",
]
GOLD_COLORS: Final[list[str]] = [
    "#ffd700", "#f5c518", "#ffe680", "#d4af37", "#fff2cc", "#e6a800",
]

# ── Minimum-card thresholds (agreed plan) ─────────────────────────────────────
DECK_MIN_ANSWERS: Final[int] = 5
ALL_DONE_MIN_ANSWERS: Final[int] = 20

# ── Gold heading ──────────────────────────────────────────────────────────────
_GOLD_TEXT_JS: Final[str] = """
(function () {
    'use strict';
    // Injected before SvelteKit paints the heading: the rule targets the
    // element directly, so its first paint is already gold. Zero flicker.
    if (document.getElementById('pf-gold-style')) return;
    const style = document.createElement('style');
    style.id = 'pf-gold-style';
    style.textContent =
        '.congrats h1{' +
        'background-image:linear-gradient(100deg,#8a6100 0%,#d4af37 18%,' +
        '#ffd700 38%,#fff6c9 50%,#ffd700 62%,#d4af37 82%,#8a6100 100%);' +
        'background-size:200% auto;background-position:0% center;' +
        '-webkit-background-clip:text;background-clip:text;' +
        'color:transparent;-webkit-text-fill-color:transparent;' +
        'animation:pf-gold-shine 3.6s ease-in-out infinite;' +
        'filter:drop-shadow(0 1px 2px rgba(90,60,0,.22))}' +
        '@keyframes pf-gold-shine{0%{background-position:0% center}' +
        '50%{background-position:100% center}100%{background-position:0% center}}' +
        '@media (prefers-reduced-motion: reduce){.congrats h1{animation:none}}';
    (document.head || document.documentElement).appendChild(style);
}());
"""

# ── JavaScript animations ─────────────────────────────────────────────────────
_CONFETTI_BURST_JS: Final[str] = """
(function () {
    'use strict';

    class ConfettiShape {
        constructor({ initialPosition, direction, confettiRadius, confettiColors, emojis, emojiSize, canvasWidth }) {
            this._setupSpeed(canvasWidth);
            this._setupRotation(emojis.length > 0, canvasWidth);
            this._setupRadius(confettiRadius);
            this._setupDirection(direction);
            this._setupPosition(initialPosition, direction);
            this._setupAppearance(confettiColors, emojis, emojiSize);
            this.createdAt = Date.now();
            this.direction = direction;
        }

        _rnd(min, max, p = 0) {
            const v = Math.random() * (max - min) + min;
            return Math.floor(v * Math.pow(10, p)) / Math.pow(10, p);
        }

        _pick(arr) { return arr[Math.floor(Math.random() * arr.length)]; }

        _setupSpeed(w) {
            const s = (Math.log(w) / Math.log(1920)) * this._rnd(0.9, 1.7, 3);
            this.speed = { x: s, y: s };
            this.finalSpeedX = this._rnd(0.2, 0.6, 3);
            this.drag = this._rnd(0.0005, 0.0009, 6);
        }

        _setupRotation(hasEmoji, w) {
            const scale = Math.log(w) / Math.log(1920);
            this.rotSpeed = hasEmoji ? 0.01 : this._rnd(0.03, 0.07, 3) * scale;
            this.emojiAngle = this._rnd(0, 2 * Math.PI);
        }

        _setupRadius(r) {
            this.radius = { x: r, y: r };
            this.initialRadius = r;
            this.radiusDir = 'down';
        }

        _setupDirection(dir) {
            const a = dir === 'left'
                ? this._rnd(82, 15) * Math.PI / 180
                : this._rnd(-15, -82) * Math.PI / 180;
            this.absCos = Math.abs(Math.cos(a));
            this.absSin = Math.abs(Math.sin(a));
            this.rotAngle = dir === 'left' ? this._rnd(0, 0.2, 3) : this._rnd(-0.2, 0, 3);
        }

        _setupPosition(pos, dir) {
            const off = this._rnd(-150, 0);
            const p = {
                x: pos.x + (dir === 'left' ? off : -off) * this.absCos,
                y: pos.y - off * this.absSin,
            };
            this.pos = { ...p };
            this.initPos = { ...p };
        }

        _setupAppearance(colors, emojis, emojiSize) {
            this.color = emojis.length > 0 ? null : this._pick(colors);
            this.emoji = emojis.length > 0 ? this._pick(emojis) : null;
            this.emojiSize = emojiSize;
        }

        draw(ctx) {
            const dpr = window.devicePixelRatio || 1;
            if (this.color) {
                ctx.fillStyle = this.color;
                ctx.beginPath();
                ctx.ellipse(
                    this.pos.x * dpr, this.pos.y * dpr,
                    this.radius.x * dpr, this.radius.y * dpr,
                    this.rotAngle, 0, 2 * Math.PI
                );
                ctx.fill();
            } else if (this.emoji) {
                ctx.font = `${this.emojiSize}px serif`;
                ctx.save();
                ctx.translate(this.pos.x * dpr, this.pos.y * dpr);
                ctx.rotate(this.emojiAngle);
                ctx.textAlign = 'center';
                ctx.fillText(this.emoji, 0, 0);
                ctx.restore();
            }
        }

        update(dt, now) {
            const elapsed = now - this.createdAt;
            if (this.speed.x > this.finalSpeedX) this.speed.x -= this.drag * dt;
            const hDir = this.direction === 'left' ? -this.absCos : this.absCos;
            this.pos.x += this.speed.x * hDir * dt;
            this.pos.y = this.initPos.y
                - this.speed.y * this.absSin * elapsed
                + 0.000625 * elapsed * elapsed;

            const decay = this.emoji ? 0.0001 : 0.00001;
            this.rotSpeed = Math.max(0, this.rotSpeed - decay * dt);
            if (this.emoji) {
                this.emojiAngle = (this.emojiAngle + this.rotSpeed * dt) % (2 * Math.PI);
            } else {
                if (this.radiusDir === 'down') {
                    this.radius.y = Math.max(0, this.radius.y - dt * this.rotSpeed);
                    if (this.radius.y <= 0) this.radiusDir = 'up';
                } else {
                    this.radius.y = Math.min(this.initialRadius, this.radius.y + dt * this.rotSpeed);
                    if (this.radius.y >= this.initialRadius) this.radiusDir = 'down';
                }
            }
        }

        isVisible(canvasHeight) { return this.pos.y < canvasHeight + 100; }
    }

    class ConfettiBatch {
        constructor(ctx) {
            this.ctx = ctx;
            this.shapes = [];
            this.promise = new Promise(r => { this._resolve = r; });
        }

        add(...shapes) { this.shapes.push(...shapes); }

        process({ timeDelta, currentTime }, canvasHeight, filter) {
            this.shapes = this.shapes.filter(s => {
                s.update(timeDelta, currentTime);
                s.draw(this.ctx);
                return !filter || s.isVisible(canvasHeight);
            });
        }

        isDone() {
            if (this.shapes.length === 0) { this._resolve(); return true; }
            return false;
        }

        get onComplete() { return this.promise; }
    }

    class JSConfetti {
        constructor(options = {}) {
            this._batches = [];
            this._rafPending = false;
            this._lastTime = Date.now();
            this._tick = 0;
            this._canvas = options.canvas ?? this._createCanvas();
            this._ctx = this._canvas.getContext('2d');
            this._loop = this._loop.bind(this);
            requestAnimationFrame(this._loop);
        }

        _createCanvas() {
            const c = document.createElement('canvas');
            Object.assign(c.style, {
                position: 'fixed', width: '100%', height: '100%',
                top: '0', left: '0', zIndex: '1000', pointerEvents: 'none',
            });
            document.body.appendChild(c);
            return c;
        }

        _resize() {
            const dpr = window.devicePixelRatio || 1;
            const cs = getComputedStyle(this._canvas);
            const w = Math.round(parseFloat(cs.width) * dpr);
            const h = Math.round(parseFloat(cs.height) * dpr);
            if (this._canvas.width !== w || this._canvas.height !== h) {
                this._canvas.width = w;
                this._canvas.height = h;
            }
        }

        _loop() {
            this._rafPending = false;
            this._resize();
            this._ctx.clearRect(0, 0, this._canvas.width, this._canvas.height);
            const now = Date.now();
            const dt = now - this._lastTime;
            const h = this._canvas.offsetHeight;
            const filter = ++this._tick % 10 === 0;

            this._batches = this._batches.filter(b => {
                b.process({ timeDelta: dt, currentTime: now }, h, filter);
                return !filter || !b.isDone();
            });

            if (this._batches.length > 0 && !this._rafPending) {
                this._rafPending = true;
                this._lastTime = now;
                requestAnimationFrame(this._loop);
            }
        }

        addConfetti(options = {}) {
            const cfg = {
                confettiRadius: options.confettiRadius ?? 6,
                confettiNumber: options.confettiNumber ?? (options.emojis?.length ? 40 : 250),
                confettiColors: options.confettiColors ?? [],
                emojis: options.emojis ?? [],
                emojiSize: options.emojiSize ?? 80,
            };

            const { width: cw, height: ch } = this._canvas.getBoundingClientRect();
            const yPos = (5 * ch) / 7;
            const batch = new ConfettiBatch(this._ctx);

            for (let i = 0; i < cfg.confettiNumber / 2; i++) {
                batch.add(
                    new ConfettiShape({ initialPosition: { x: 0, y: yPos }, direction: 'right', canvasWidth: cw, ...cfg }),
                    new ConfettiShape({ initialPosition: { x: cw, y: yPos }, direction: 'left', canvasWidth: cw, ...cfg }),
                );
            }

            this._batches.push(batch);
            if (!this._rafPending) {
                this._rafPending = true;
                this._lastTime = Date.now();
                requestAnimationFrame(this._loop);
            }
            return batch.onComplete;
        }

        clearCanvas() { this._batches = []; }
    }

    if (!window.__jsConfetti) window.__jsConfetti = new JSConfetti();
    window.__jsConfetti.addConfetti({ confettiColors: __CONFETTI_COLORS__ });
}());
"""

_CONFETTI_RAIN_JS: Final[str] = """
(function () {
    'use strict';

    const COLORS = __CONFETTI_COLORS__;
    const DURATION_MS = 7000;
    const SPAWN_RATE_PER_SECOND = 34;
    const STAR_CHANCE = 0.12;
    const INITIAL_SEED_COUNT = 44;

    function drawStar(ctx, cx, cy, spikes, outerRadius, innerRadius) {
        let rot = (Math.PI / 2) * 3;
        let x = cx;
        let y = cy;
        const step = Math.PI / spikes;
        ctx.beginPath();
        ctx.moveTo(cx, cy - outerRadius);
        for (let i = 0; i < spikes; i++) {
            x = cx + Math.cos(rot) * outerRadius;
            y = cy + Math.sin(rot) * outerRadius;
            ctx.lineTo(x, y);
            rot += step;
            x = cx + Math.cos(rot) * innerRadius;
            y = cy + Math.sin(rot) * innerRadius;
            ctx.lineTo(x, y);
            rot += step;
        }
        ctx.lineTo(cx, cy - outerRadius);
        ctx.closePath();
        ctx.fill();
    }

    class ConfettiPiece {
        constructor(canvasWidth, canvasHeight, seeded) {
            this.baseX = Math.random() * canvasWidth;
            this.x = this.baseX;
            this.y = seeded ? Math.random() * canvasHeight * 0.9 - 40 : -20;
            this.isStar = Math.random() < STAR_CHANCE;
            this.color = COLORS[Math.floor(Math.random() * COLORS.length)];
            this.width = Math.random() * 6 + 8;
            this.height = this.isStar ? this.width : Math.random() * 10 + 10;
            this.fallSpeed = Math.random() * 1.5 + 1.8;
            this.swaySpeed = Math.random() * 0.02 + 0.01;
            this.swayAmplitude = Math.random() * 40 + 20;
            this.swayOffset = Math.random() * Math.PI * 2;
            this.rotation = Math.random() * Math.PI * 2;
            this.rotationSpeed = (Math.random() - 0.5) * 0.15;
            this.tick = 0;
            this.twinkle = Math.random() * Math.PI * 2;
        }

        update() {
            this.tick += 1;
            this.y += this.fallSpeed;
            this.x = this.baseX + Math.sin(this.tick * this.swaySpeed + this.swayOffset) * this.swayAmplitude;
            this.rotation += this.rotationSpeed;
            if (this.isStar) this.twinkle += 0.15;
        }

        draw(ctx, canvasHeight) {
            const edgeFade = Math.max(0, Math.min(1, (canvasHeight + 20 - this.y) / 90));
            ctx.save();
            ctx.translate(this.x, this.y);
            ctx.rotate(this.rotation);
            if (this.isStar) {
                const glow = 0.6 + 0.4 * Math.sin(this.twinkle);
                ctx.globalAlpha = glow * edgeFade;
                ctx.fillStyle = this.color;
                ctx.shadowColor = this.color;
                ctx.shadowBlur = 6;
                drawStar(ctx, 0, 0, 4, this.width / 2, this.width / 4);
            } else {
                const flip = Math.cos(this.rotation * 2);
                ctx.scale(flip, 1);
                ctx.globalAlpha = edgeFade;
                ctx.fillStyle = this.color;
                ctx.fillRect(-this.width / 2, -this.height / 2, this.width, this.height);
            }
            ctx.restore();
        }

        isOffscreen(canvasHeight) {
            return this.y > canvasHeight + 40;
        }
    }

    class ConfettiRain {
        constructor() {
            this._canvas = this._createCanvas();
            this._ctx = this._canvas.getContext('2d');
            this._pieces = [];
            this._startedAt = Date.now();
            this._lastFrame = Date.now();
            this._spawnAccumulator = 0;
            this._loop = this._loop.bind(this);
        }

        _createCanvas() {
            const c = document.createElement('canvas');
            Object.assign(c.style, {
                position: 'fixed', width: '100%', height: '100%',
                top: '0', left: '0', zIndex: '1000', pointerEvents: 'none',
            });
            document.body.appendChild(c);
            return c;
        }

        _resize() {
            const dpr = window.devicePixelRatio || 1;
            const cs = getComputedStyle(this._canvas);
            const w = Math.round(parseFloat(cs.width) * dpr);
            const h = Math.round(parseFloat(cs.height) * dpr);
            if (this._canvas.width !== w || this._canvas.height !== h) {
                this._canvas.width = w;
                this._canvas.height = h;
                this._ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
            }
        }

        start() {
            this._resize();
            const dpr = window.devicePixelRatio || 1;
            const w = this._canvas.width / dpr;
            const h = this._canvas.height / dpr;
            for (let i = 0; i < INITIAL_SEED_COUNT; i++) {
                this._pieces.push(new ConfettiPiece(w, h, true));
            }
            requestAnimationFrame(this._loop);
        }

        _loop() {
            const now = Date.now();
            const dt = now - this._lastFrame;
            this._lastFrame = now;
            const elapsed = now - this._startedAt;

            const dpr = window.devicePixelRatio || 1;
            const w = this._canvas.width / dpr;
            const h = this._canvas.height / dpr;

            if (elapsed < DURATION_MS) {
                this._spawnAccumulator += (SPAWN_RATE_PER_SECOND * dt) / 1000;
                while (this._spawnAccumulator >= 1) {
                    this._pieces.push(new ConfettiPiece(w, h, false));
                    this._spawnAccumulator -= 1;
                }
            }

            this._ctx.clearRect(0, 0, w, h);
            this._pieces.forEach(p => { p.update(); p.draw(this._ctx, h); });
            this._pieces = this._pieces.filter(p => !p.isOffscreen(h));

            if (elapsed < DURATION_MS || this._pieces.length > 0) {
                requestAnimationFrame(this._loop);
            } else {
                this._canvas.remove();
            }
        }
    }

    new ConfettiRain().start();
}());
"""


def _burst_js(colors: list[str]) -> str:
    return _CONFETTI_BURST_JS.replace("__CONFETTI_COLORS__", json.dumps(colors))


def _rain_js(colors: list[str]) -> str:
    return _CONFETTI_RAIN_JS.replace("__CONFETTI_COLORS__", json.dumps(colors))


# ── Collection queries ────────────────────────────────────────────────────────
def _deck_remaining(col: Collection) -> int:
    return sum(col.sched.counts())


def _global_remaining(col: Collection) -> int:
    tree = col.sched.deck_due_tree()
    return tree.new_count + tree.learn_count + tree.review_count


@dataclass(frozen=True, slots=True)
class _Remaining:
    deck: int
    total: int


# ── Counters ──────────────────────────────────────────────────────────────────
@dataclass(slots=True)
class SessionStats:
    answers: int = 0
    perfect: bool = True

    def record(self, correct: bool) -> None:
        self.answers += 1
        if not correct:
            self.perfect = False

    def reset(self) -> None:
        self.answers = 0
        self.perfect = True


class ConfettiManager:
    __slots__ = (
        "_session",
        "_entered_review",
        "_day",
        "_day_answers",
        "_day_perfect",
        "_get_config",
    )

    def __init__(self, get_config: Callable[[], AddonConfig]) -> None:
        self._get_config: Callable[[], AddonConfig] = get_config
        self._session: SessionStats = SessionStats()
        self._entered_review: bool = False
        self._day: datetime.date = datetime.date.today()
        self._day_answers: int = 0
        self._day_perfect: bool = True
        self._restore_day()

    # ── day state persisted in the addon config ───────────────────────────────
    def _restore_day(self) -> None:
        state = load_day_state()
        if state.date == self._day.isoformat():
            self._day_answers = state.answers
            self._day_perfect = state.perfect

    def _persist_day(self) -> None:
        save_day_state(
            DayState(
                date=self._day.isoformat(),
                answers=self._day_answers,
                perfect=self._day_perfect,
            )
        )

    def _rollover(self) -> None:
        today = datetime.date.today()
        if today != self._day:
            self._day = today
            self._day_answers = 0
            self._day_perfect = True
            self._persist_day()

    # ── hooks ─────────────────────────────────────────────────────────────────
    def register(self) -> None:
        gui_hooks.state_did_change.append(self._on_state_did_change)
        gui_hooks.overview_did_refresh.append(self._on_overview_refresh)

    def unregister(self) -> None:
        for hook, handler in (
            (gui_hooks.state_did_change, self._on_state_did_change),
            (gui_hooks.overview_did_refresh, self._on_overview_refresh),
        ):
            try:
                hook.remove(handler)
            except ValueError:
                pass

    def reset(self) -> None:
        try:
            self._persist_day()
        except Exception as error:
            log_error("ConfettiManager.reset", error)
        self._session.reset()
        self._entered_review = False

    def record_answer(self, correct: bool) -> None:
        try:
            self._rollover()
            self._session.record(correct)
            self._day_answers += 1
            if not correct:
                self._day_perfect = False
        except Exception as error:
            log_error("ConfettiManager.record_answer", error)

    def _on_state_did_change(self, new_state: str, old_state: str) -> None:
        try:
            if new_state == "review":
                self._rollover()
                self._session.reset()
                self._entered_review = True
        except Exception as error:
            log_error("ConfettiManager._on_state_did_change", error)

    def _on_overview_refresh(self, overview: Overview) -> None:
        try:
            if mw is None or mw.web is None or mw.col is None:
                return
            if not self._entered_review:
                return
            self._entered_review = False
            if self._session.answers <= 0:
                return
            self._evaluate_and_fire()
        except Exception as error:
            log_error("ConfettiManager._on_overview_refresh", error)

    # ── decision + firing ─────────────────────────────────────────────────────
    def _evaluate_and_fire(self) -> None:
        from .audio import has_sounds, play_named
        from .constants import (
            FIN_MAZO_DIR,
            FIN_TODO_DIR,
            PERFECTO_MAZO_DIR,
            PERFECTO_TODO_DIR,
        )

        config: AddonConfig = self._get_config()
        sounds_on = config.sessionSoundsEnabled
        confetti_on = config.confettiEnabled
        if not (sounds_on or confetti_on):
            return

        deck_sound = config.deckFinishSound
        all_sound = config.allDoneSound
        deck_perfect_sound = config.deckPerfectSound
        all_perfect_sound = config.allPerfectSound

        def play_finish(gold: bool, perfect_dir: str, perfect_name: str,
                        normal_dir: str, normal_name: str) -> None:
            # Gold moments get their own sound; empty folder falls back to normal.
            if gold and has_sounds(perfect_dir):
                play_named(perfect_dir, perfect_name)
            else:
                play_named(normal_dir, normal_name)

        session_answers = self._session.answers
        session_perfect = self._session.perfect
        self._rollover()
        self._persist_day()
        day_answers = self._day_answers
        day_perfect = self._day_perfect

        def op(col: Collection) -> _Remaining:
            return _Remaining(deck=_deck_remaining(col), total=_global_remaining(col))

        def on_success(remaining: _Remaining) -> None:
            try:
                if mw is None or mw.web is None:
                    return
                if remaining.total == 0:
                    all_gold = day_answers >= ALL_DONE_MIN_ANSWERS and day_perfect
                    if sounds_on:
                        play_finish(all_gold, PERFECTO_TODO_DIR, all_perfect_sound,
                                    FIN_TODO_DIR, all_sound)
                    if confetti_on and day_answers >= ALL_DONE_MIN_ANSWERS:
                        if day_perfect:
                            mw.web.eval(_GOLD_TEXT_JS)
                            mw.web.eval(_rain_js(GOLD_COLORS))
                        else:
                            mw.web.eval(_rain_js(NORMAL_COLORS))
                elif remaining.deck == 0:
                    deck_gold = session_answers >= DECK_MIN_ANSWERS and session_perfect
                    if sounds_on:
                        play_finish(deck_gold, PERFECTO_MAZO_DIR, deck_perfect_sound,
                                    FIN_MAZO_DIR, deck_sound)
                    if confetti_on and session_answers >= DECK_MIN_ANSWERS:
                        if session_perfect:
                            mw.web.eval(_GOLD_TEXT_JS)
                            mw.web.eval(_burst_js(GOLD_COLORS))
                        else:
                            mw.web.eval(_burst_js(NORMAL_COLORS))
            except Exception as error:
                log_error("ConfettiManager.on_success", error)

        def on_failure(error: Exception) -> None:
            log_error("ConfettiManager.background", error)

        op_obj = QueryOp(parent=mw, op=op, success=on_success).failure(on_failure)
        if hasattr(op_obj, "without_collection_lock"):
            op_obj = op_obj.without_collection_lock()
        op_obj.run_in_background()