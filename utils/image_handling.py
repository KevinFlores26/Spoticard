import requests
from PyQt5.QtGui import QPixmap, QImage
from PIL import Image
from io import BytesIO
from colorthief import ColorThief
from typing import TYPE_CHECKING, Union

from utils.helpers import apply_rounded_corners
from utils.color_handling import Color
from utils.file_handling import File

if TYPE_CHECKING: # Imports only for type annotations purposes (ignored at runtime)
  from requests import Response
  from PIL.Image import ImageFile

class ExtractImageColor:
  def __init__(self) -> None:
    self.img_bytes: BytesIO | None = None
    self.color_thief: ColorThief | None = None
    self.palette: list[tuple[int, int, int]] | None = None

    self.accent_color: tuple[int, int, int] | None = None
    self.accent_saturation: float = 0.0

  def extract(self, img_src: str, card_color: str) -> str | None:
    self.set_img_bytes(img_src)

    if not self.img_bytes:
      return None

    self.color_thief: ColorThief = ColorThief(self.img_bytes)
    self.palette = self.color_thief.get_palette(color_count=10, quality=1)
    self.accent_color = self.color_thief.get_color(quality=1)

    if len(self.palette) < 1:
      hex_color: str = "#%02x%02x%02x" % self.accent_color
      return hex_color

    card_rgb_color: tuple[int, int, int] = Color.hex_to_rgb(card_color)
    card_lightness: float = Color().get_rgb_lightness(card_rgb_color)

    for color in self.palette:
      card_color_distance: float = Color.color_distance(color, card_rgb_color)
      _, lightness, saturation = Color.rgb_to_hls(color)

      # If color is too close to card color, skip
      if card_color_distance < 100 or abs(lightness - card_lightness) < 0.20:
        continue
      # Get the color with the highest saturation
      if saturation < self.accent_saturation:
        continue

      self.accent_saturation = saturation
      self.accent_color = color

    hex_color: str = "#%02x%02x%02x" % self.accent_color
    return hex_color

  def set_img_bytes(self, img_src: str) -> None:
    if not img_src or not isinstance(img_src, (str, bytes)):
      return

    elif isinstance(img_src, bytes):
      self.img_bytes = BytesIO(img_src)
      return

    try:
      if img_src.startswith("http"):
        response: "Response" = requests.get(img_src)
        if response.status_code != 200:
          return

        img_data: bytes = response.content
        self.img_bytes = BytesIO(img_data)

      else:
        self.img_bytes = File.get_relative_path(img_src)

    except Exception as e:
      print(f"Error: Image not found or not supported ({e})")


class ConvertImageToPixmap:
  def __init__(self) -> None:
    self.img: Union["ImageFile", None] = None
    self.pixmap: QPixmap | None = None

  def convert(self, img_src: str, img_size: str, radius: int = 5) -> QPixmap | None:
    self.set_img(img_src)
    self.img = self.img.resize((img_size, img_size), Image.Resampling.LANCZOS)
    self.img = self.img.convert("RGBA")

    data: bytes = self.img.tobytes("raw", "RGBA")
    q_image: QImage = QImage(data, self.img.width, self.img.height, QImage.Format_RGBA8888)
    self.pixmap = QPixmap.fromImage(q_image)

    if radius > 0:
      self.pixmap = apply_rounded_corners(self.pixmap, radius)

    return self.pixmap

  def set_img(self, img_src: str) -> None:
    if not img_src or not isinstance(img_src, (str, bytes)):
      return

    elif isinstance(img_src, bytes):
      self.img = Image.open(BytesIO(img_src))
      return

    try:
      if img_src.startswith("http"):
        response: "Response" = requests.get(img_src)
        if response.status_code != 200:
          return

        img_data: bytes = response.content
        self.img = Image.open(BytesIO(img_data))

      else:
        img_path: str = File.get_relative_path(img_src)
        self.img = Image.open(img_path)

    except Exception as e:
      print(f"Error: Image not found or not supported ({e})")
