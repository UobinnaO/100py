# milo_simple.py (rewritten with fixes 1–4)
import asyncio
import csv
import random
from dataclasses import dataclass, field
from enum import Enum
from typing import Protocol, Callable, Awaitable, Optional, Tuple

# --- PIL (pure rendering) ---
from PIL import Image, ImageDraw, ImageFont

# --- Toga only at the edges (adapter impl) ---
import toga
from toga.constants import CENTER
from toga.style.pack import Pack

# =========================
# Domain data (values only)
# =========================


@dataclass(frozen=True)
class WordPair:
    fr: str
    en: str


@dataclass(frozen=True)
class ThemeSpec:
    front_path: str
    back_path: str
    title_font_path: str
    word_font_path: str
    title_font_size: int = 40
    word_font_size: int = 60
    canvas_size: Tuple[int, int] = (800, 526)
    title_pos: Tuple[int, int] = (400, 175)
    word_pos: Tuple[int, int] = (400, 350)
    title_color: str = "red"
    word_color: str = "green"

    def key(self) -> Tuple:
        # Pure, hashable descriptor of the visual theme
        return (
            self.front_path,
            self.back_path,
            self.title_font_path,
            self.word_font_path,
            self.title_font_size,
            self.word_font_size,
            self.canvas_size,
            self.title_pos,
            self.word_pos,
            self.title_color,
            self.word_color,
        )


@dataclass(frozen=True)
class Theme:
    spec: ThemeSpec
    base_front: Image.Image
    base_back: Image.Image
    title_font: ImageFont.FreeTypeFont
    word_font: ImageFont.FreeTypeFont

    @property
    def key(self) -> Tuple:
        return self.spec.key()


@dataclass(frozen=True)
class CardImages:
    front: Image.Image
    back: Image.Image


# =========================
# Rules layer (policies)
# =========================


class SelectionPolicy(Protocol):
    def initial(self, corpus: tuple[WordPair, ...]) -> WordPair: ...
    def next(self, current: WordPair, corpus: tuple[WordPair, ...]) -> WordPair: ...


class RandomSelection:
    def initial(self, corpus: tuple[WordPair, ...]) -> WordPair:
        return random.choice(corpus)

    def next(self, current: WordPair, corpus: tuple[WordPair, ...]) -> WordPair:
        if not corpus:
            return current
        nxt = random.choice(corpus)
        return nxt if nxt != current else random.choice(corpus)


@dataclass(frozen=True)
class FlipPolicy:
    # Single source of truth for timing + enablement
    interval_sec: float = 5.0
    auto_flip: bool = True


# =========================
# Rendering (pure + cache)
# =========================


@dataclass
class CardRenderer:
    theme: Theme
    _cache: dict[Tuple[str, str, Tuple], CardImages] = field(default_factory=dict)

    def render(self, words: WordPair) -> CardImages:
        key = (words.fr, words.en, self.theme.key)
        imgs = self._cache.get(key)
        if imgs:
            return imgs

        f = self.theme.base_front.copy()
        b = self.theme.base_back.copy()

        df = ImageDraw.Draw(f)
        df.text(
            self.theme.spec.title_pos,
            "French",
            anchor="mm",
            font=self.theme.title_font,
            fill=self.theme.spec.title_color,
        )
        df.text(
            self.theme.spec.word_pos,
            words.fr,
            anchor="mm",
            font=self.theme.word_font,
            fill=self.theme.spec.word_color,
        )

        db = ImageDraw.Draw(b)
        db.text(
            self.theme.spec.title_pos,
            "English",
            anchor="mm",
            font=self.theme.title_font,
            fill=self.theme.spec.title_color,
        )
        db.text(
            self.theme.spec.word_pos,
            words.en,
            anchor="mm",
            font=self.theme.word_font,
            fill=self.theme.spec.word_color,
        )

        imgs = CardImages(front=f, back=b)
        self._cache[key] = imgs
        return imgs


# =========================
# Events (typed, no strings)
# =========================


class Event(Enum):
    FLIP = "flip"
    NEXT = "next"


# =========================
# Ports (inversion)
# =========================


class ViewPort(Protocol):
    def show(self, front: Image.Image, back: Image.Image, show_back: bool) -> None: ...
    def update_side(self, show_back: bool) -> None: ...


class Scheduler(Protocol):
    async def run(self, publish: Callable[[Event], Awaitable[None]]) -> None: ...


# =========================
# Adapters (edge-only Toga)
# =========================

TARGET_W, TARGET_H = 540, 420


class TogaViewPort(ViewPort):
    """Wraps a dedicated slot container; no domain leakage."""

    def __init__(self, slot: toga.Box, width: int = TARGET_W, height: int = TARGET_H):
        self.slot = slot  # dedicated container we control
        self.width = width
        self.height = height
        self.front_view: Optional[toga.ImageView] = None
        self.back_view: Optional[toga.ImageView] = None
        self._showing_back = False

    def show(self, front: Image.Image, back: Image.Image, show_back: bool) -> None:
        # Fix 1: copy() here to avoid aliasing cached images
        self.front_view = toga.ImageView(
            front.copy(), style=Pack(width=self.width, height=self.height)
        )
        self.back_view = toga.ImageView(
            back.copy(), style=Pack(width=self.width, height=self.height)
        )
        self._showing_back = show_back
        view = self.back_view if show_back else self.front_view
        if self.slot.children:
            self.slot.replace(self.slot.children[0], view)
        else:
            self.slot.add(view)

    def update_side(self, show_back: bool) -> None:
        if self.front_view is None or self.back_view is None:
            return
        if show_back == self._showing_back:
            return
        self._showing_back = show_back
        new_view = self.back_view if show_back else self.front_view
        if self.slot.children:
            self.slot.replace(self.slot.children[0], new_view)
        else:
            self.slot.add(new_view)


class IntervalScheduler(Scheduler):
    """Timing policy comes from FlipPolicy (single authority)."""

    def __init__(self, policy: FlipPolicy, event: Event = Event.FLIP):
        self.policy = policy
        self.event = event

    async def run(self, publish: Callable[[Event], Awaitable[None]]) -> None:
        if not self.policy.auto_flip:
            return
        while True:
            await asyncio.sleep(self.policy.interval_sec)
            await publish(self.event)


# =========================
# Event bus (decoupled flow)
# =========================


class AsyncEventBus:
    def __init__(self):
        self._q: asyncio.Queue[Event] = asyncio.Queue()
        self._handlers: list[Callable[[Event], None]] = []

    def subscribe(self, handler: Callable[[Event], None]) -> None:
        self._handlers.append(handler)

    async def publish(self, evt: Event) -> None:
        await self._q.put(evt)

    async def pump(self) -> None:
        while True:
            evt = await self._q.get()
            for h in list(self._handlers):
                h(evt)


# =========================
# Controller (pure-ish app)
# =========================


class Controller:
    """No Toga types here; coordinates domain, rendering, viewport, and events."""
    def __init__(
        self,
        corpus: tuple[WordPair, ...],
        renderer: CardRenderer,
        viewport: ViewPort,
        selection: SelectionPolicy,
        flip_policy: FlipPolicy,
        bus: AsyncEventBus,
    ):
        self.corpus = corpus
        self.renderer = renderer
        self.viewport = viewport
        self.selection = selection
        self.flip_policy = flip_policy

        self.current: WordPair = self.selection.initial(self.corpus)
        self.showing_back: bool = False

        self._render_and_show()

        bus.subscribe(self._on_event)

    # intents
    def flip(self) -> None:
        self.showing_back = not self.showing_back
        self.viewport.update_side(self.showing_back)

    def next(self) -> None:
        self.current = self.selection.next(self.current, self.corpus)
        # reset to front; policy choice, but explicit:
        self.showing_back = False
        self._render_and_show()

    # internal
    def _render_and_show(self) -> None:
        imgs = self.renderer.render(self.current)
        self.viewport.show(imgs.front, imgs.back, self.showing_back)

    # event handler (typed)
    def _on_event(self, evt: Event) -> None:
        if evt is Event.FLIP and self.flip_policy.auto_flip:
            self.flip()
        elif evt is Event.NEXT:
            self.next()


# =========================
# Loading utilities (pure)
# =========================


def load_csv_word_pairs(path: str) -> tuple[WordPair, ...]:
    out: list[WordPair] = []
    with open(path, newline="", encoding="utf-8") as f:
        rdr = csv.reader(f)
        for row in rdr:
            if len(row) < 2:
                continue
            fr, en = row[0].strip(), row[1].strip()
            if (fr, en) == ("French", "English"):
                continue
            out.append(WordPair(fr=fr, en=en))
    return tuple(out)


def load_theme(spec: ThemeSpec) -> Theme:
    title_font = ImageFont.truetype(spec.title_font_path, spec.title_font_size)
    word_font = ImageFont.truetype(spec.word_font_path, spec.word_font_size)
    base_front = Image.open(spec.front_path)
    base_back = Image.open(spec.back_path)
    return Theme(
        spec=spec,
        base_front=base_front,
        base_back=base_back,
        title_font=title_font,
        word_font=word_font,
    )


# =========================
# Toga App (wiring only)
# =========================


class Milo(toga.App):
    def startup(self) -> None:
        # --- load values ---
        corpus = load_csv_word_pairs("resources/data/french_words.csv")
        theme_spec = ThemeSpec(
            front_path="resources/images/card_front.png",
            back_path="resources/images/card_back.png",
            title_font_path="resources/fonts/Roboto-Italic.ttf",
            word_font_path="resources/fonts/Roboto-Bold.ttf",
        )
        theme = load_theme(theme_spec)
        renderer = CardRenderer(theme)

        # --- UI skeleton (adapter host) ---
        self.main_window = toga.MainWindow()
        wrapper = toga.Column(
            style=Pack(align_items=CENTER, justify_content=CENTER, padding=10)
        )
        page = toga.Column(
            style=Pack(flex=1, align_items=CENTER, justify_content=CENTER, padding=10)
        )
        body = toga.Row(style=Pack())
        footer = toga.Row(style=Pack(gap=20))
        page.add(body, footer)
        wrapper.add(page)
        self.main_window.content = wrapper
        self.main_window.show()

        # Dedicated card slot to avoid positional coupling
        card_slot = toga.Box(style=Pack())
        body.add(card_slot)

        viewport = TogaViewPort(card_slot)

        # --- event bus + scheduler injection ---
        self.bus = AsyncEventBus()

        # --- rules/policies (single authority for interval) ---
        flip_policy = FlipPolicy(interval_sec=5.0, auto_flip=True)
        self.flip_sched = IntervalScheduler(policy=flip_policy, event=Event.FLIP)

        selection = RandomSelection()

        # --- controller ---
        self.controller = Controller(
            corpus=corpus,
            renderer=renderer,
            viewport=viewport,
            selection=selection,
            flip_policy=flip_policy,
            bus=self.bus,
        )

        # --- tasks (edges only) ---
        asyncio.create_task(self.bus.pump())
        asyncio.create_task(self.flip_sched.run(self.bus.publish))

        # --- buttons (emit typed events, not mutate UI) ---
        next_btn = toga.Button(
            "Next", on_press=lambda b: asyncio.create_task(self.bus.publish(Event.NEXT))
        )
        flip_btn = toga.Button(
            "Flip", on_press=lambda b: asyncio.create_task(self.bus.publish(Event.FLIP))
        )
        footer.add(next_btn, flip_btn)


def main():
    return Milo("Milo", "org.example.milo")


if __name__ == "__main__":
    main().main_loop()
