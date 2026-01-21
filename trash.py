import toga
from toga.style.pack import Pack
from toga import Key

STEP = 10


class App(toga.App):
    def startup(self):
        self.canvas = toga.Canvas(style=Pack(flex=1))

        # Draw one square, then just move it by changing properties + redraw.
        with self.canvas.context.Fill(color="red") as fill:
            self.square = fill.rect(x=50, y=50, width=30, height=30)

        self.main_window = toga.MainWindow(title=self.formal_name)
        self.main_window.content = self.canvas

        # Arrow keys -> commands (discrete activations)
        self.commands.add(
            toga.Command(lambda w: self.move(-STEP, 0), text="Left", shortcut=Key.LEFT),
            toga.Command(
                lambda w: self.move(+STEP, 0), text="Right", shortcut=Key.RIGHT
            ),
            toga.Command(lambda w: self.move(0, -STEP), text="Up", shortcut=Key.UP),
            toga.Command(lambda w: self.move(0, +STEP), text="Down", shortcut=Key.DOWN),
        )

        self.main_window.show()

    def move(self, dx, dy):
        self.square.x += dx
        self.square.y += dy
        self.canvas.redraw()


def main():
    return App("Toga Move Square", "org.example.movesquare")


if __name__ == "__main__":
    main().main_loop()
