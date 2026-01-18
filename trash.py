from __future__ import annotations

import asyncio
import csv
import random
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Tuple

import toga
from toga.constants import CENTER
from toga.style.pack import Pack

from PIL import Image, ImageDraw, ImageFont


# =========================
# Domain data (values only)
# =========================


@dataclass(frozen=True)
class WordPair:
    fr: str
    en: str


@dataclass(frozen=True)
class CardImages:
    # NOTE: Core holds Pillow images only (UI-agnostic)
    front: Image.Image
    back: Image.Image


@dataclass(frozen=True)
class Theme:
    base_front: Image.Image
    base_back: Image.Image
    title_font: ImageFont.FreeTypeFont
    word_font: ImageFont.FreeTypeFont
    canvas_size: Tuple[int, int] = (800, 526)
    title_pos: Tuple[int, int] = (400, 175)
    word_pos: Tuple[int, int] = (400, 350)
    title_color: str = "red"
    word_color: str = "green"


# --------- App model (pure) ---------


@dataclass(frozen=True)
class Model:
    current: WordPair
    showing_back: bool = False


def update(model: Model, msg: str, word_pairs: tuple[WordPair, ...]) -> Model:
    if msg == "flip" and not model.showing_back:
        return replace(model, showing_back=True)
    if msg == "next":
        return replace(model, current=random.choice(word_pairs), showing_back=False)
    return model


def render(model: Model, theme: Theme) -> CardImages:
    return render_card(model.current, theme)


TARGET_W, TARGET_H = 540, 420
AUTO_FLIP_DELAY_S = 5.0
BG = "#b4ddc7"


# =========================
# Pure rendering (no UI)
# =========================


def render_card(words: WordPair, theme: Theme) -> CardImages:
    front_pil = theme.base_front.copy()
    back_pil = theme.base_back.copy()

    df = ImageDraw.Draw(front_pil)
    df.text(
        theme.title_pos,
        "French",
        anchor="mm",
        font=theme.title_font,
        fill=theme.title_color,
    )
    df.text(
        theme.word_pos,
        words.fr,
        anchor="mm",
        font=theme.word_font,
        fill=theme.word_color,
    )

    db = ImageDraw.Draw(back_pil)
    db.text(
        theme.title_pos,
        "English",
        anchor="mm",
        font=theme.title_font,
        fill=theme.title_color,
    )
    db.text(
        theme.word_pos,
        words.en,
        anchor="mm",
        font=theme.word_font,
        fill=theme.word_color,
    )

    # Core returns PIL images only
    return CardImages(front=front_pil, back=back_pil)


# =========================
# Loading helpers
# =========================


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


def load_theme(resources: Path) -> Theme:
    title_font = ImageFont.truetype(str(resources / "fonts" / "Roboto-Italic.ttf"), 40)
    word_font = ImageFont.truetype(str(resources / "fonts" / "Roboto-Bold.ttf"), 60)
    base_front = Image.open(resources / "images" / "card_front.png")
    base_back = Image.open(resources / "images" / "card_back.png")
    return Theme(
        base_front=base_front,
        base_back=base_back,
        title_font=title_font,
        word_font=word_font,
    )


# =========================
# App (UI edge)
# =========================


class Milo(toga.App):
    def startup(self) -> None:
        resources = self.paths.app / "resources"

        # Data
        self.word_pairs = load_word_pairs(resources / "data" / "french_words.csv")
        self.theme = load_theme(resources)

        # Model (pure state)
        self.model = Model(current=random.choice(self.word_pairs))

        # Initial render (PIL in core) → pass PIL directly to Toga
        imgs = render(self.model, self.theme)

        # UI widgets
        self.card_view = toga.ImageView(
            image=imgs.front,  # PIL image directly
            style=Pack(width=TARGET_W, height=TARGET_H),
        )

        self.wrong_btn = toga.Button(
            icon=toga.Icon(resources / "images" / "wrong.png"),
            on_press=self.on_flip,
            style=Pack(background_color=BG),
        )
        self.right_btn = toga.Button(
            icon=toga.Icon(resources / "images" / "right.png"),
            on_press=self.on_next,
            style=Pack(background_color=BG),
        )

        # Layout (Box + Pack directions)
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
        main_window.content = self.wrapper
        main_window.show()
        self.main_window = main_window

        # Decoupled timing: producer/consumer via queue
        self.events: asyncio.Queue[str] = asyncio.Queue()
        # asyncio.create_task(self._scheduler())  # produces "flip"
        # asyncio.create_task(self._ui_consumer())  # consumes events

    # ----- Event producer: WHEN -----
    async def _scheduler(self) -> None:
        while True:
            await asyncio.sleep(AUTO_FLIP_DELAY_S)
            if not self.model.showing_back:
                await self.events.put("flip")
                print("flip enter")

    # ----- Event consumer: WHAT (UI edge) -----
    async def _ui_consumer(self) -> None:
        while True:
            msg = await self.events.get()
            self.model = update(self.model, msg, self.word_pairs)
            self._refresh_view()

    # ----- View refresh from model -----
    def _refresh_view(self) -> None:
        imgs = render(self.model, self.theme)
        self.card_view.image = imgs.back if self.model.showing_back else imgs.front

    # ----- Button callbacks (send messages) -----
    def on_flip(self, button: toga.Button) -> None:
        self.events.put_nowait("flip")

    def on_next(self, button: toga.Button) -> None:
        self.events.put_nowait("next")


def main() -> Milo:
    return Milo("Milo", "org.example.milo")


if __name__ == "__main__":
    main().main_loop()
