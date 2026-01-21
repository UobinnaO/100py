# =========================
# [LEGEND: Simple Made Easy labels]
# [VALUES]       = prefer immutable values over state
# [WHAT]         = pure transformations (specify "what")
# [HOW]          = effectful edges (I/O, UI, timers) that implement "how/when/where"
# [DATA>SYNTAX]  = prefer plain data, tiny interfaces
# [QUEUES]       = decouple doer from doing (when/where via queue)
# [SMALL-IFACE]  = small surface areas / explicit intents
# [NOTE]         = brief rationale or TODO aligned with the talk
# =========================

from __future__ import annotations

import asyncio
import csv
import random
from dataclasses import dataclass, replace
from enum import Enum, auto
from pathlib import Path
from typing import Tuple, Any

import toga
from toga.constants import CENTER
from toga.style.pack import Pack
from PIL import Image, ImageDraw, ImageFont

# =========================
# Domain data (values only)
# =========================

BG = "#b4ddc7"


# [VALUES][DATA>SYNTAX] plain, immutable domain items
@dataclass(frozen=True)
class WordPair:
    fr: str
    en: str


# [VALUES] container for already-rendered images (value semantics at call sites)
@dataclass(frozen=True)
class CardImages:
    # Core holds Pillow images only (UI-agnostic)
    front: Image.Image
    back: Image.Image


# [VALUES][DATA>SYNTAX] theme/config as pure data (no I/O here)
@dataclass(frozen=True)
class Theme:
    # Preloaded, value-only assets (no I/O during render)
    base_front_img: Image.Image
    base_back_img: Image.Image
    title_font: ImageFont.FreeTypeFont
    word_font: ImageFont.FreeTypeFont
    # canvas_size: Tuple[int, int] = (800, 526)
    canvas_size: Tuple[int, int] = (600, 526)
    title_pos: Tuple[int, int] = (400, 175)
    word_pos: Tuple[int, int] = (400, 350)


# [VALUES] keep policy as data; separates policy from behavior implementation
@dataclass(frozen=True)
class Policy:
    front_title: str = "French"
    back_title: str = "English"
    title_color: str = "red"
    word_color: str = "green"
    flip_delay_s: float = 5.0  # timing policy


# --------- App model (pure) ---------


# [VALUES] model is an immutable snapshot of state
@dataclass(frozen=True)
class Model:
    current: WordPair
    showing_back: bool = False


# [WHAT] pure, no time/randomness; returns a new model
def flip(model: Model) -> Model:
    """Pure: front -> back (no time/randomness)."""
    if model.showing_back:
        return model
    return replace(model, showing_back=True)


# [WHAT] pure; selection happens at the edge and is passed in
def next_card(model: Model, chosen: WordPair) -> Model:
    """Pure: swap to a specific next card (chosen at the edge)."""
    return replace(model, current=chosen, showing_back=False)


# [WHAT] rendering is a pure function of (model, theme, policy)
def render(model: Model, theme: Theme, policy: Policy) -> CardImages:
    return render_card(model.current, theme, policy)


# =========================
# Pure rendering (no UI)
# =========================


# [WHAT][DATA>SYNTAX] render uses only data; no disk/net I/O; copies to ·eserve value semantics
def render_card(words: WordPair, theme: Theme, policy: Policy) -> CardImages:
    # Copy preloaded base images (value semantics); no disk or font I/O here
    front_pil = theme.base_front_img.copy()
    back_pil = theme.base_back_img.copy()
    df = ImageDraw.Draw(front_pil)
    df.text(
        theme.title_pos,
        policy.front_title,
        anchor="mm",
        font=theme.title_font,
        fill=policy.title_color,
    )
    df.text(
        theme.word_pos,
        words.fr,
        anchor="mm",
        font=theme.word_font,
        fill=policy.word_color,
    )

    db = ImageDraw.Draw(back_pil)
    db.text(
        theme.title_pos,
        policy.back_title,
        anchor="mm",
        font=theme.title_font,
        fill=policy.title_color,
    )
    db.text(
        theme.word_pos,
        words.en,
        anchor="mm",
        font=theme.word_font,
        fill=policy.word_color,
    )

    return CardImages(front=front_pil, back=back_pil)


# =========================
# Loading helpers
# =========================


# [HOW] edge I/O (CSV). Converts to [VALUES] for the pure core.
def load_word_pairs(csv_path: Path) -> tuple[WordPair, ...]:
    rows: list[WordPair] = []
    with csv_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        # Expect headers: French,English
        for row in reader:
            fr = (row.get("French") or "").strip()
            en = (row.get("English") or "").strip()
            if fr and en:
                rows.append(WordPair(fr=fr, en=en))
    return tuple(rows)


# [HOW] edge I/O (FS/font decode). Returns pure Theme [VALUES].
def load_theme(resources: Path) -> Theme:
    # Preload images and fonts once; hand pure values to render()
    base_front = Image.open(resources / "images" / "card_front.png").convert("RGBA")
    base_back = Image.open(resources / "images" / "card_back.png").convert("RGBA")
    title_font = ImageFont.truetype(str(resources / "fonts" / "Roboto-Italic.ttf"), 40)
    word_font = ImageFont.truetype(str(resources / "fonts" / "Roboto-Bold.ttf"), 60)
    return Theme(
        base_front_img=base_front,
        base_back_img=base_back,
        title_font=title_font,
        word_font=word_font,
    )


# =========================
# Events (when/where decoupled)
# =========================


# [SMALL-IFACE] tiny, explicit intents; can grow to RIGHT/WRONG without braiding
class Event(Enum):
    NEXT = auto()
    AUTO_FLIP = auto()


# =========================
# App (UI edge)
# =========================


class Milo(toga.App):
    def startup(self) -> None:
        resources = self.paths.app / "resources"

        # Data
        # [HOW] edge loads; passes [VALUES] into core
        self.word_pairs = load_word_pairs(resources / "data" / "french_words.csv")
        self.theme = load_theme(resources)
        self.policy = Policy()

        # Model (pure state)
        # [HOW] randomness lives at edge; chosen value fed into [WHAT]
        self.model = Model(current=random.choice(self.word_pairs))

        # UI widgets (Toga ImageView accepts PIL images)
        # [WHAT] render → [HOW] assign to UI
        imgs = render(self.model, self.theme, self.policy)
        w, h = self.theme.canvas_size
        self.card_view = toga.ImageView(
            image=imgs.front,
            style=Pack(width=w, height=h),
        )

        # [SMALL-IFACE] buttons emit intents (no state change here)
        self.wrong_btn = toga.Button(
            icon=toga.Icon(resources / "images" / "wrong.png"),
            on_press=self.on_next,  # edge: emit intent only
            style=Pack(background_color=BG),
        )
        self.right_btn = toga.Button(
            icon=toga.Icon(resources / "images" / "right.png"),
            on_press=self.on_next,  # edge: emit intent only
            style=Pack(background_color=BG),
        )

        # Layout
        self.body = toga.Box(
            style=Pack(
                direction="row",
                background_color=BG,
                align_items=CENTER,
                justify_content=CENTER,
            )
        )
        self.body.add(self.card_view)

        self.footer = toga.Box(
            style=Pack(
                direction="row",
                background_color=BG,
                align_items=CENTER,
                justify_content=CENTER,
                gap=250,
                margin_top=10,
            )
        )
        self.footer.add(self.wrong_btn, self.right_btn)

        self.page = toga.Box(
            style=Pack(
                direction="column",
                flex=1,
                margin=10,
                background_color=BG,
                align_items=CENTER,
                justify_content=CENTER,
            )
        )
        self.page.add(self.body, self.footer)

        self.wrapper = toga.Box(
            style=Pack(
                direction="column",
                flex=1,
                background_color=BG,
                align_items=CENTER,
                justify_content=CENTER,
            )
        )
        self.wrapper.add(self.page)

        main_window = toga.MainWindow(title="Milo")
        # main_window = toga.MainWindow(title="Milo", resizable=False)
        main_window.content = self.wrapper

        # IMPORTANT: attach the close handler to the *window object* you created.
        # (Your original code used self.main_window before self.main_window existed.)
        main_window.on_close = self.on_close  # [HOW] lifecycle edge

        main_window.show()
        self.main_window = main_window

        # ---- Event system ----
        # [QUEUES] decouple when/where from what; centralize sequencing
        self.event_queue: asyncio.Queue[Event] = asyncio.Queue()

        # Keep task handles so we can cancel on exit.
        self.flip_task: asyncio.Task[None] | None = None
        self.reducer_task: asyncio.Task[None] | None = None

        # NOTE: Don't create asyncio tasks here; startup() can run before the
        # asyncio loop is considered "running" on some Toga backends.

    def on_running(self, **kwargs: Any) -> None:
        # IMPORTANT: Toga's docs allow async handlers, but current type stubs often
        # model on_running() as a normal (non-async) method returning None.
        # This wrapper keeps your runtime behavior AND satisfies type checkers.

        # [HOW][QUEUES] create event loop tasks after app loop starts (time = edge)
        # Create tasks here (guaranteed: app event loop has started).
        # Use the app's loop explicitly (avoid asyncio.get_running_loop()).
        if self.reducer_task is None or self.reducer_task.done():
            self.reducer_task = self.loop.create_task(self._run_loop())

        # Kick off first timed flip
        self._start_flip_timer(
            self.policy.flip_delay_s
        )  # [WHEN] scheduling at the edge

    # ----- View refresh -----
    # [HOW] UI binding layer; consumes pure render output; no domain logic here
    def _refresh_view(self) -> None:
        imgs = render(self.model, self.theme, self.policy)
        self.card_view.image = imgs.back if self.model.showing_back else imgs.front

    # ----- Event reducer loop (single "when/where") -----
    # [WHAT+WHEN NOTE] reducer updates model (what) *and* triggers timers (when) — a tiny braid.
    # [NOTE] If desired, return "effects" from reducer and apply here to fully unbraid.
    async def _run_loop(self) -> None:
        try:
            while True:
                event = await self.event_queue.get()
                if event is Event.NEXT:
                    chosen = random.choice(
                        self.word_pairs
                    )  # [HOW] randomness at the edge
                    self.model = next_card(self.model, chosen)  # [WHAT]
                    self._start_flip_timer(self.policy.flip_delay_s)  # [WHEN]
                elif event is Event.AUTO_FLIP and not self.model.showing_back:
                    self.model = flip(self.model)  # [WHAT]
                self._refresh_view()
        except asyncio.CancelledError:
            # Normal shutdown path (window close cancels reducer_task)
            return

    # ----- Timer management -----
    # [WHEN/WHERE] explicit time handling at the boundary (clock edge)
    def _cancel_flip_timer(self) -> None:
        t = getattr(self, "flip_task", None)
        if t and not t.done():
            t.cancel()

    def _start_flip_timer(self, delay_s: float) -> None:
        self._cancel_flip_timer()

        async def _later() -> None:
            try:
                await asyncio.sleep(delay_s)  # [WHEN]
                await self.event_queue.put(
                    Event.AUTO_FLIP
                )  # [QUEUES] schedule next intent
            except asyncio.CancelledError:
                pass

        # Use the app loop explicitly (matches the BeeWare handlers example style,
        # but avoids relying on a "running loop" lookup).
        self.flip_task = self.loop.create_task(_later())

    # ----- Button callbacks (edges emit intents) -----
    # [SMALL-IFACE][QUEUES] translate UI actions into intents; no state mutation here
    def on_next(self, button: toga.Button) -> None:
        # No state change here; just emit intent
        self.event_queue.put_nowait(Event.NEXT)

    def on_close(self, window: toga.Window, **kwargs: Any) -> bool:
        # [HOW] lifecycle edge: cancel time + worker tasks; keep core pure
        # Clean shutdown of tasks
        self._cancel_flip_timer()
        rt = getattr(self, "reducer_task", None)
        if rt and not rt.done():
            rt.cancel()
        return True


# [HOW] composition root; wires edges and core
def main() -> Milo:
    return Milo("Milo", "org.example.milo")


if __name__ == "__main__":
    main().main_loop()
