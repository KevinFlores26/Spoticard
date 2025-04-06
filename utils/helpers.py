import threading
from PyQt5.QtCore import Qt, QRectF, QTimer
from PyQt5.QtGui import QPixmap, QPainter, QPainterPath
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # Imports only for type annotations purposes (ignored at runtime)
  from PyQt5.QtCore import QSize

# Auxiliary functions
def set_timer(callback: callable) -> QTimer:
  # Sets a timer and return it
  timer: QTimer = QTimer()
  timer.timeout.connect(callback)
  return timer


def debounce(wait):
  # Debounce a function
  def decorator(fn):
    def debounced(*args, **kwargs):
      def call_it():
        fn(*args, **kwargs)

      if hasattr(debounced, '_timer'):
        debounced._timer.cancel()
      debounced._timer = threading.Timer(wait / 1000, call_it)
      debounced._timer.start()

    return debounced

  return decorator


def apply_rounded_corners(pixmap: QPixmap, radius: int) -> QPixmap:
  # Apply rounded corners to a pixmap and return it
  size: "QSize" = pixmap.size()
  rounded_pixmap: QPixmap = QPixmap(size)
  rounded_pixmap.fill(Qt.transparent)

  painter: QPainter = QPainter(rounded_pixmap)
  painter.setRenderHint(QPainter.Antialiasing)

  # Set rounded corners
  path: QPainterPath = QPainterPath()
  path.addRoundedRect(QRectF(0, 0, size.width(), size.height()), radius, radius)
  painter.setClipPath(path)

  painter.drawPixmap(0, 0, pixmap)
  painter.end()
  return rounded_pixmap
