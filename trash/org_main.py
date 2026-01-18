import asyncio
from random import choices, randint
import toga
from dataclasses import dataclass, field
from settings import *

txt_stream = open(join("resources", "data", "french_words.csv"))

lines = txt_stream.readlines()

word_pairs = [[]]
# print(word_pairs[0][0])

for line in lines:
    strip_line = line.strip()
    split_line = strip_line.split(",")
    if split_line == ["French", "English"]:
        continue
    word_pairs.append(split_line)

title_font = ImageFont.truetype("resources/fonts/Roboto-Italic.ttf", 40)
word_font = ImageFont.truetype("resources/fonts/Roboto-Bold.ttf", 60)
card_front = Image.open("resources/images/card_front.png")
card_back = Image.open("resources/images/card_back.png")
TARGET_W, TARGET_H = 540, 420
# TARGET_W, TARGET_H = 1000, 1000


def render_card(words) -> tuple[Image.Image, Image.Image]:
    # no global mutation; create new front/back from templates and return them
    ...


def _make_front():
    return card_front.copy()


def _make_back():
    return card_back.copy()


@dataclass
class CardGraphic:
    front: Image.Image = field(default_factory=_make_front)
    back: Image.Image = field(default_factory=_make_back)


def create_card(graphic: CardGraphic, words: list):
    cfront_size = (800, 526)
    if pil_present:
        img_canvas = ImageDraw.Draw(graphic.front)
        img_canvas.text(
            (cfront_size[0] / 2, cfront_size[1] / 3),
            "French",
            fill="red",
            anchor="mm",
            font=title_font,
        )
        img_canvas.text(
            (cfront_size[0] / 2, cfront_size[1] / 1.5),
            f"{words[0]}",
            fill="green",
            anchor="mm",
            font=word_font,
        )

    if pil_present:
        img_canvas = ImageDraw.Draw(graphic.back)
        img_canvas.text(
            (cfront_size[0] / 2, cfront_size[1] / 3),
            "English",
            fill="red",
            anchor="mm",
            font=title_font,
        )
        img_canvas.text(
            (cfront_size[0] / 2, cfront_size[1] / 1.5),
            f"{words[1]}",
            fill="green",
            anchor="mm",
            font=word_font,
        )
    # card front card back
    card_front = toga.ImageView(
        graphic.front, style=Pack(width=TARGET_W, height=TARGET_H)
    )
    card_back = toga.ImageView(
        graphic.back, style=Pack(width=TARGET_W, height=TARGET_H)
    )

    return Card(card_front, card_back)


@dataclass
class Card:
    front: toga.ImageView
    back: toga.ImageView


class Milo(toga.App):

    def startup(self) -> None:
        self.showing_back = False

        # self.main_window = toga.MainWindow()
        self.main_window = toga.MainWindow()

        self.wrapper = toga.Column(
            style=Pack(
                background_color=RED,
                align_items=CENTER,
                justify_content=CENTER,
            ),
        )
        self.page = toga.Column(
            style=Pack(
                flex=1,
                background_color=BLUE,
                # gap=10,
                padding=10,
                align_items=CENTER,
                justify_content=CENTER,
            )
        )
        # self.header = toga.Row(style=Pack(flex=1, background_color=BURLYWOOD))
        # self.body = toga.Row(style=Pack(flex=1, background_color=GREEN))
        self.body = toga.Row(style=Pack(background_color=GREEN))
        self.footer = toga.Row(
            # style=Pack(background_color=YELLOW, width=300, height=100, gap=10)
            style=Pack(background_color=YELLOW, gap=250)
        )

        self.current_word_pair = choice(word_pairs)
        self.card_graphic = CardGraphic()
        self.card = create_card(self.card_graphic, self.current_word_pair)

        right_button = toga.Button(
            icon=toga.Icon("resources/images/right.png"),
            on_press=self.change_card,
        )
        wrong_button = toga.Button(
            icon=toga.Icon("resources/images/wrong.png"),
            on_press=self.change_card,
        )

        # Add to header/body/footer
        self.body.add(self.card.front)
        self.footer.add(right_button, wrong_button)

        # Add nodes
        self.page.add(self.body, self.footer)
        self.wrapper.add(self.page)

        # # Add the content on the main window
        self.main_window.content = self.wrapper

        # Show the main window
        self.main_window.show()

        self.card = create_card(self.card_graphic, self.current_word_pair)
        asyncio.create_task(self.call_flip_card())

    # * funcs
    async def call_flip_card(self):
        while True:
            await asyncio.sleep(5)
            self.flip_card()

    def flip_card(self):
        self.showing_back = not self.showing_back
        self.body.replace(
            self.body.children[0],
            self.card_back if self.showing_back else self.card_front,
        )

    def change_card(self, button):
        pass
        # print(f"old pair: {self.current_word_pair}")
        # self.current_word_pair = choice(word_pairs)
        # card_front_copy = card_front.copy()
        # card_back_copy = card_back.copy()
        # print(f"new cur pair {self.current_word_pair}")

        # if pil_present:
        #     img_canvas = ImageDraw.Draw(card_front_copy)
        #     img_canvas.text(
        #         (self.cfront_size[0] / 2, self.cfront_size[1] / 3),
        #         "French",
        #         fill="red",
        #         anchor="mm",
        #         font=title_font,
        #     )
        #     img_canvas.text(
        #         (self.cfront_size[0] / 2, self.cfront_size[1] / 1.5),
        #         f"{self.current_word_pair[0]}",
        #         fill="green",
        #         anchor="mm",
        #         font=word_font,
        #     )

        # if pil_present:
        #     img_canvas = ImageDraw.Draw(card_back_copy)
        #     img_canvas.text(
        #         (self.cfront_size[0] / 2, self.cfront_size[1] / 3),
        #         "English",
        #         fill="red",
        #         anchor="mm",
        #         font=title_font,
        #     )
        #     img_canvas.text(
        #         (self.cfront_size[0] / 2, self.cfront_size[1] / 1.5),
        #         f"{self.current_word_pair[1]}",
        #         fill="green",
        #         anchor="mm",
        #         font=word_font,
        #     )
        # # card front card back
        # # if self.body.children[0] == self.card_front or self.body.children[0] == self.card_back:
        # if self.body.children[0]:
        #     new_card_front = toga.ImageView(
        #         card_front_copy, style=Pack(width=TARGET_W, height=TARGET_H)
        #     )
        #     new_card_back = toga.ImageView(
        #         card_back_copy, style=Pack(width=TARGET_W, height=TARGET_H)
        #     )
        #     self.card = (new_card_front, new_card_back)
        #     # if self.body.children[0] == self.card[0] or self.body.children[0] == self.card[1]:
        #     #     print('Yes')
        #     # else:
        #     #     print('No')
        #     self.body.replace(self.body.children[0], self.card[0])
        # asyncio.create_task(self.call_flip_card(self.card))


def main():
    return Milo("Milo", "com.tnkvie.milo")


if __name__ == "__main__":
    main().main_loop()

#     # print(dir(self.body.children[0]))  # attributes & methods
#     # print("===========================")
#     # print(vars(self.body.children[0]))  # __dict__ contents (if it has one)

#     # for attr in dir(self.body.children[0]):
#     #     print(attr)

#     # if hasattr(self.body.children[0], "__dict__"):
#     #     for key, value in vars(self.body.children[0]).items():
#     #         print(f"{key} = {value}")
#     # else:
#     print("Object has no __dict__")

# for attr in dir(self.body.children[0]):
#     try:
#         value = getattr(self.body.children[0], attr)
#         print(f"{attr} = {value}")
#     except Exception as e:
#         print(f"{attr} -> Error: {e}")

# print("===========================")
# print(repr(self.body.children[0]))
# print(self.body.children[0])
# print(self.body.children[0].__dict__)

# for attr in dir(self.new_card_back):
#     try:
#         value = getattr(self.new_card_back, attr)
#         print(f"{attr} = {value}")
#     except Exception as e:
#         print(f"{attr} -> Error: {e}")

# getattr(self, "new_card_back")
# if self.new_card_back not in self.body.children:
# attr_name = self.body.children[].name
# or whatever property stores the name
# print(getattr(self, self.body.children[0]))

# if self.body.children[0] != self.new_card_back:
# if getattr(self, f"{self.body.children[0]}")
# self.body.children[0] = self.card_front
# self.card_front = self.body.children[0]
# if self.new_card_back not in self.body.children:
#     self.new_card_back = toga.ImageView(
#         card_back,
#     )
# if self.body.children[0] != self.new_card_back:
#     self.body.children[0] = self.card_front
#     self.body.replace(self.card_front, self.new_card_back)
#     self.card_front = self.body.children[0]

#     pass
