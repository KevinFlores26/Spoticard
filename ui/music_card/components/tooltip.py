from typing import TYPE_CHECKING
from PyQt5.QtGui import QCursor
from PyQt5.QtWidgets import QLabel
from utils.helpers import set_timer

if TYPE_CHECKING: # Imports only for type annotations purposes (ignored at runtime)
  from PyQt5.QtCore import QPoint, QTimer
  from ui.music_card.card import MusicCard

class Tooltip:
  def __init__(self, card: "MusicCard") -> None:
    self.card = card
    self.tooltip_timer: "QTimer" = set_timer(self.show_tooltip)

    self.tooltip: QLabel = QLabel("Tooltip", self.card)
    self.tooltip.setStyleSheet(f"color: white; font-size: 10px; font-family: Poppins, Arial;")
    self.tooltip.adjustSize()
    self.tooltip.hide()

  def get_tooltip(self) -> QLabel:
    return self.tooltip

  def show_tooltip(self):
    self.card.tooltip_timer.stop()
    global_pos: QPoint = QCursor.pos()
    widget_pos: QPoint = self.card.mapFromGlobal(global_pos)
    print(widget_pos)
    self.card.cursor_coords = widget_pos

    # if self.tooltip_visible or self.is_dragging:
    #  return
    # elif not self.tooltip_visible and :

    self.tooltip.show()
    self.card.tooltip_visible = True
