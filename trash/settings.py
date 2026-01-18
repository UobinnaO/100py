from sys import argv
import os
import time
from random import choice, randint, randbytes
from os.path import join

try:
    import PIL.Image
    import PIL.ImageDraw

    pil_present = True
except ImportError: 
    pil_present = False
import toga
from toga.style import Pack
from PIL import Image, ImageDraw, ImageFont
from toga.constants import (
    BLUE,
    RED,
    CENTER,
    BOLD,
    COLUMN,
    ITALIC,
    MONOSPACE,
    NORMAL,
    ROW,
    YELLOW,
    GREEN,
    BLACK,
    SILVER,
    GOLD,
    BURLYWOOD,
)
