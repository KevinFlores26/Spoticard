import math
from colorsys import rgb_to_hls

class Color:
  @staticmethod
  def hex_to_rgb(hex_color: str) -> tuple[int, int, int] | None:
    # Convert a hex color code (string) to a tuple of RGB values
    if not hex_color.startswith("#"):
      return None

    hex_color = hex_color.lstrip("#")
    red, green, blue = tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
    return red, green, blue

  @staticmethod
  def color_distance(color1: tuple[int, int, int], color2: tuple[int, int, int]) -> float:
    # Calculate the distance between two colors
    r_diff: int = color1[0] - color2[0]
    g_diff: int = color1[1] - color2[1]
    b_diff: int = color1[2] - color2[2]
    return math.sqrt(r_diff ** 2 + g_diff ** 2 + b_diff ** 2)

  @staticmethod
  def rgb_to_hls(rgb: tuple[int, int, int]) -> tuple[float, float, float] | None:
    if len(rgb) != 3:
      return None

    r, g, b = [x / 255.0 for x in rgb]
    hue, lightness, saturation = rgb_to_hls(r, g, b)
    return hue, lightness, saturation

  def get_rgb_saturation(self, rgb: tuple[int, int, int]) -> float:
    hue, lightness, saturation = self.rgb_to_hls(rgb)
    return saturation

  def get_rgb_lightness(self, rgb: tuple[int, int, int]) -> float:
    hue, lightness, saturation = self.rgb_to_hls(rgb)
    return lightness
