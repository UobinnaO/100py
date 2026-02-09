# milo_raylib.py
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

import csv
import random
from collections import deque
from dataclasses import dataclass, replace
from enum import Enum, auto
from pathlib import Path
from typing import Tuple

import pyray as rl  # pyray = snake_case wrapper over raylib C API :contentReference[oaicite:3]{index=3}
import settings as cfg

# =========================
# Domain data (values only)
# =========================

BG = "#b4ddc7"


# [VALUES][DATA>SYNTAX] plain, immutable domain items
@dataclass(frozen=True)
class WordPair:
    fr: str
    en: str


# [VALUES][DATA>SYNTAX] config as pure data
@dataclass(frozen=True)
class ThemeSpec:
    canvas_size: Tuple[int, int] = (800, 526)
    title_pos: Tuple[int, int] = (400, 175)  # center within card
    word_pos: Tuple[int, int] = (400, 350)  # center within card
    title_font_size: int = 40
    word_font_size: int = 60
    text_spacing: float = 2.0  # raylib spacing


# [VALUES] keep policy as data
@dataclass(frozen=True)
class Policy:
    front_title: str = "French"
    back_title: str = "English"
    title_color: str = "red"
    word_color: str = "green"
    flip_delay_s: float = 5.0


# --------- App model (pure) ---------


# [VALUES] model is an immutable snapshot of state
@dataclass(frozen=True)
class Model:
    current: WordPair
    showing_back: bool = False


# [WHAT] pure, no time/randomness
def flip(model: Model) -> Model:
    if model.showing_back:
        return model
    return replace(model, showing_back=True)


# [WHAT] pure; selection happens at the edge and is passed in
def next_card(model: Model, chosen: WordPair) -> Model:
    return replace(model, current=chosen, showing_back=False)


# =========================
# Loading helpers
# =========================


# [HOW] edge I/O (CSV). Converts to [VALUES] for the pure core.
def load_word_pairs(csv_path: Path) -> tuple[WordPair, ...]:
    rows: list[WordPair] = []
    with csv_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            fr = (row.get("French") or "").strip()
            en = (row.get("English") or "").strip()
            if fr and en:
                rows.append(WordPair(fr=fr, en=en))
    return tuple(rows)


# =========================
# Events (when/where decoupled)
# =========================


# [SMALL-IFACE] tiny, explicit intents
class Event(Enum):
    NEXT = auto()
    AUTO_FLIP = auto()


# =========================
# Raylib-specific helpers
# =========================


# [HOW] UI color decode at the boundary
def hex_to_color(s: str) -> rl.Color:
    s = s.lstrip("#")
    r = int(s[0:2], 16)
    g = int(s[2:4], 16)
    b = int(s[4:6], 16)
    return rl.Color(r, g, b, 255)


# [HOW] policy colors mapped at the boundary (expand as needed)
def color_from_name(name: str) -> rl.Color:
    name = name.lower()
    table = {
        "red": rl.RED,
        "green": rl.GREEN,
        "black": rl.BLACK,
        "white": rl.RAYWHITE,
        "gray": rl.GRAY,
    }
    return table.get(name, rl.BLACK)


# [HOW] centered text (raylib has no "anchor=mm"; we measure and offset)
def draw_text_centered(
    font: rl.Font,
    text: str,
    center_xy: Tuple[float, float],
    font_size: float,
    spacing: float,
    color: rl.Color,
) -> None:
    size = rl.measure_text_ex(font, text, font_size, spacing)
    pos = rl.Vector2(center_xy[0] - size.x / 2.0, center_xy[1] - size.y / 2.0)
    rl.draw_text_ex(font, text, pos, font_size, spacing, color)


# =========================
# App (raylib loop edge)
# =========================


def main() -> None:
    # [HOW] composition root: locate resources
    here = Path(__file__).resolve().parent
    resources = here / "resources"
    data_csv = resources / "data" / "french_words.csv"

    # [HOW] load data once
    word_pairs = load_word_pairs(data_csv)
    if not word_pairs:
        raise SystemExit("No word pairs loaded (check CSV headers French,English).")

    theme = ThemeSpec()
    policy = Policy()

    # val = cfg.asset("resources","images","card_front.png")
    # val2 =
    # print(f"\n{val}")

    # [HOW] init window (immediate-mode UI) :contentReference[oaicite:4]{index=4}
    win_w, win_h = 900, 720
    rl.init_window(win_w, win_h, "Milo (raylib)")
    rl.set_target_fps(60)

    bg_color = hex_to_color(BG)

    # [HOW] load textures/fonts once (GPU + font decode)
    card_front = rl.load_texture(cfg.asset("resources", "images", "card_front.png"))
    card_back = rl.load_texture(str(resources / "images" / "card_back.png"))
    wrong_tex = rl.load_texture(str(resources / "images" / "wrong.png"))
    right_tex = rl.load_texture(str(resources / "images" / "right.png"))
    # card_front = rl.load_texture(str(resources / "images" / "card_front.png"))
    title_font = rl.load_font_ex(
        str(resources / "fonts" / "Roboto-Italic.ttf"), theme.title_font_size, None, 0
    )
    word_font = rl.load_font_ex(
        str(resources / "fonts" / "Roboto-Bold.ttf"), theme.word_font_size, None, 0
    )

    # Model (pure state)
    # [HOW] randomness at edge
    model = Model(current=random.choice(word_pairs))

    # ---- Event system ----
    # [QUEUES] decouple input/time from pure updates
    events: deque[Event] = deque()

    # [WHEN] timer state at the boundary
    time_since_next = 0.0

    # Layout (edge/UI concerns)
    card_w, card_h = theme.canvas_size
    card_x = (win_w - card_w) // 2
    card_y = 60

    # Buttons hitboxes
    btn_size = 80
    btn_y = card_y + card_h + 35
    wrong_x = (win_w // 2) - 200
    right_x = (win_w // 2) + 120
    wrong_rect = rl.Rectangle(wrong_x, btn_y, btn_size, btn_size)
    right_rect = rl.Rectangle(right_x, btn_y, btn_size, btn_size)

    # Main loop
    while not rl.window_should_close():  # :contentReference[oaicite:5]{index=5}
        # [WHEN] frame-time (seconds) :contentReference[oaicite:6]{index=6}
        dt = rl.get_frame_time()
        time_since_next += dt

        # [WHEN -> QUEUES] schedule auto-flip intent (no direct mutation here)
        if (not model.showing_back) and (time_since_next >= policy.flip_delay_s):
            events.append(Event.AUTO_FLIP)

        # [HOW -> QUEUES] input edge emits intents :contentReference[oaicite:7]{index=7}
        if rl.is_mouse_button_pressed(rl.MOUSE_BUTTON_LEFT):
            mp = rl.get_mouse_position()
            if rl.check_collision_point_rec(
                mp, wrong_rect
            ) or rl.check_collision_point_rec(mp, right_rect):
                events.append(Event.NEXT)

        # Optional keyboard shortcuts (edge)
        if rl.is_key_pressed(rl.KEY_SPACE):
            events.append(Event.NEXT)

        # [QUEUES] reducer: single sequencing point
        while events:
            ev = events.popleft()
            if ev is Event.NEXT:
                chosen = random.choice(word_pairs)  # [HOW] randomness at edge
                model = next_card(model, chosen)  # [WHAT]
                time_since_next = 0.0  # [WHEN] reset timer at edge
            elif ev is Event.AUTO_FLIP:
                model = flip(model)  # [WHAT]

        # Draw (edge)
        rl.begin_drawing()
        rl.clear_background(bg_color)

        # Card base
        tex = card_back if model.showing_back else card_front
        rl.draw_texture(tex, card_x, card_y, rl.WHITE)

        # Text overlay (computed from pure model + policy)
        title = policy.back_title if model.showing_back else policy.front_title
        word = model.current.en if model.showing_back else model.current.fr

        title_center = (card_x + theme.title_pos[0], card_y + theme.title_pos[1])
        word_center = (card_x + theme.word_pos[0], card_y + theme.word_pos[1])

        draw_text_centered(
            title_font,
            title,
            title_center,
            float(theme.title_font_size),
            theme.text_spacing,
            color_from_name(policy.title_color),
        )
        draw_text_centered(
            word_font,
            word,
            word_center,
            float(theme.word_font_size),
            theme.text_spacing,
            color_from_name(policy.word_color),
        )

        # Buttons (simple sprites + hitboxes)
        rl.draw_rectangle_lines_ex(wrong_rect, 2, rl.BLACK)
        rl.draw_rectangle_lines_ex(right_rect, 2, rl.BLACK)
        rl.draw_texture_ex(
            wrong_tex,
            rl.Vector2(wrong_x, btn_y),
            0.0,
            btn_size / max(1, wrong_tex.width),
            rl.WHITE,
        )
        rl.draw_texture_ex(
            right_tex,
            rl.Vector2(right_x, btn_y),
            0.0,
            btn_size / max(1, right_tex.width),
            rl.WHITE,
        )

        rl.end_drawing()

    # [HOW] shutdown edge
    rl.unload_texture(card_front)
    rl.unload_texture(card_back)
    rl.unload_texture(wrong_tex)
    rl.unload_texture(right_tex)
    rl.unload_font(title_font)
    rl.unload_font(word_font)
    rl.close_window()


if __name__ == "__main__":
    main()
