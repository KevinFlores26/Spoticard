import math
import os
from PyQt5 import QtCore, QtGui
from PyQt5.QtCore import QEasingCurve as Ease

EASING_FUNCTIONS = {
  "InSine": Ease.InSine,
  "OutSine": Ease.OutSine,
  "InOutSine": Ease.InOutSine,
  "InQuad": Ease.InQuad,
  "OutQuad": Ease.OutQuad,
  "InOutQuad": Ease.InOutQuad,
  "InCubic": Ease.InCubic,
  "OutCubic": Ease.OutCubic,
  "InOutCubic": Ease.InOutCubic,
  "InQuart": Ease.InQuart,
  "OutQuart": Ease.OutQuart,
  "InOutQuart": Ease.InOutQuart,
  "InQuint": Ease.InQuint,
  "OutQuint": Ease.OutQuint,
  "InOutQuint": Ease.InOutQuint,
  "InExpo": Ease.InExpo,
  "OutExpo": Ease.OutExpo,
  "InOutExpo": Ease.InOutExpo,
  "InCirc": Ease.InCirc,
  "OutCirc": Ease.OutCirc,
  "InOutCirc": Ease.InOutCirc,
  "InBack": Ease.InBack,
  "OutBack": Ease.OutBack,
  "InOutBack": Ease.InOutBack,
  "InElastic": Ease.InElastic,
  "OutElastic": Ease.OutElastic,
  "InOutElastic": Ease.InOutElastic,
  "InBounce": Ease.InBounce,
  "OutBounce": Ease.OutBounce,
  "InOutBounce": Ease.InOutBounce,
}

# Auxiliary functions
def get_relative_path(file_path):
  # Get the path to the file relative to the project root
  project_root = os.path.dirname(os.path.dirname(__file__))
  relative_path = os.path.join(project_root, file_path)
  return relative_path


def hex_to_rgb(hex_color):
  # Convert a hex color code (string) to a tuple of RGB values
  if not hex_color.startswith("#"):
    return hex_color

  hex_color = hex_color.lstrip("#")
  return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))


def color_distance(color1, color2):
  # Calculate the distance between two colors
  r_diff = color1[0] - color2[0]
  g_diff = color1[1] - color2[1]
  b_diff = color1[2] - color2[2]
  return math.sqrt(r_diff ** 2 + g_diff ** 2 + b_diff ** 2)


def apply_rounded_corners(pixmap, radius):
  # Apply rounded corners to a pixmap and return it
  size = pixmap.size()
  rounded_pixmap = QtGui.QPixmap(size)
  rounded_pixmap.fill(QtCore.Qt.transparent)

  painter = QtGui.QPainter(rounded_pixmap)
  painter.setRenderHint(QtGui.QPainter.Antialiasing)

  # Set rounded corners
  path = QtGui.QPainterPath()
  path.addRoundedRect(QtCore.QRectF(0, 0, size.width(), size.height()), radius, radius)
  painter.setClipPath(path)

  painter.drawPixmap(0, 0, pixmap)
  painter.end()
  return rounded_pixmap
