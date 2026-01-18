import asyncio
from random import choices, randint
import toga
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


class Milo(toga.App):

    def startup(self) -> None:
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

        self.cfront_size = (800, 526)
        self.current_word_pair = choice(word_pairs)
        base_card_front = card_front.copy()
        base_card_back = card_back.copy()
        if pil_present:
            img_canvas = ImageDraw.Draw(base_card_front)
            img_canvas.text(
                (self.cfront_size[0] / 2, self.cfront_size[1] / 3),
                "French",
                fill="red",
                anchor="mm",
                font=title_font,
            )
            img_canvas.text(
                (self.cfront_size[0] / 2, self.cfront_size[1] / 1.5),
                f"{self.current_word_pair[0]}",
                fill="green",
                anchor="mm",
                font=word_font,
            )

        if pil_present:
            img_canvas = ImageDraw.Draw(base_card_back)
            img_canvas.text(
                (self.cfront_size[0] / 2, self.cfront_size[1] / 3),
                "English",
                fill="red",
                anchor="mm",
                font=title_font,
            )
            img_canvas.text(
                (self.cfront_size[0] / 2, self.cfront_size[1] / 1.5),
                f"{self.current_word_pair[1]}",
                fill="green",
                anchor="mm",
                font=word_font,
            )
        # card front card back
        self.card_front = toga.ImageView(
            base_card_front, style=Pack(width=TARGET_W, height=TARGET_H)
        )
        self.card_back = toga.ImageView(
            base_card_back, style=Pack(width=TARGET_W, height=TARGET_H)
        )

        right_button = toga.Button(
            icon=toga.Icon("resources/images/right.png"),
            on_press=self.change_card,
        )
        wrong_button = toga.Button(
            icon=toga.Icon("resources/images/wrong.png"),
            on_press=self.change_card,
        )

        # Add to header/body/footer
        self.body.add(self.card_front)
        self.footer.add(right_button, wrong_button)

        # Add nodes
        self.page.add(self.body, self.footer)
        self.wrapper.add(self.page)

        # # Add the content on the main window
        self.main_window.content = self.wrapper

        # Show the main window
        self.main_window.show()

        self.card = (self.card_front, self.card_back)
        asyncio.create_task(self.call_flip_card(self.card))

    # * funcs
    async def call_flip_card(self, card):
        while True:
            await asyncio.sleep(10)
            self.flip_card(card)

    def flip_card(self, card):
        if not self.current_word_pair:
            return
        # if self.body.children[0] != self.card_back:
        if self.body.children[0] != card[1]:
            # self.body.replace(self.card_front, self.card_back)
            self.body.replace(card[0], card[1])

    def change_card(self, button):
        print(f"old pair: {self.current_word_pair}")
        self.current_word_pair = choice(word_pairs)
        card_front_copy = card_front.copy()
        card_back_copy = card_back.copy()
        print(f"new cur pair {self.current_word_pair}")

        if pil_present:
            img_canvas = ImageDraw.Draw(card_front_copy)
            img_canvas.text(
                (self.cfront_size[0] / 2, self.cfront_size[1] / 3),
                "French",
                fill="red",
                anchor="mm",
                font=title_font,
            )
            img_canvas.text(
                (self.cfront_size[0] / 2, self.cfront_size[1] / 1.5),
                f"{self.current_word_pair[0]}",
                fill="green",
                anchor="mm",
                font=word_font,
            )

        if pil_present:
            img_canvas = ImageDraw.Draw(card_back_copy)
            img_canvas.text(
                (self.cfront_size[0] / 2, self.cfront_size[1] / 3),
                "English",
                fill="red",
                anchor="mm",
                font=title_font,
            )
            img_canvas.text(
                (self.cfront_size[0] / 2, self.cfront_size[1] / 1.5),
                f"{self.current_word_pair[1]}",
                fill="green",
                anchor="mm",
                font=word_font,
            )
        # card front card back
        # if self.body.children[0] == self.card_front or self.body.children[0] == self.card_back:
        if self.body.children[0]:
            new_card_front = toga.ImageView(
                card_front_copy, style=Pack(width=TARGET_W, height=TARGET_H)
            )
            new_card_back = toga.ImageView(
                card_back_copy, style=Pack(width=TARGET_W, height=TARGET_H)
            )
            self.card = (new_card_front, new_card_back)
            # if self.body.children[0] == self.card[0] or self.body.children[0] == self.card[1]:
            #     print('Yes')
            # else:
            #     print('No')
            self.body.replace(self.body.children[0], self.card[0])
            asyncio.create_task(self.call_flip_card(self.card))


def main():
    return Milo("Milo", "com.tnkvie.milo")


if __name__ == "__main__":
    main().main_loop()
