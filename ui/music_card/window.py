from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMainWindow
from typing import TYPE_CHECKING

from config.config_main import config
from ui.music_card.card import MusicCard
from ui.music_card.handlers import ScreenHandler, ShortcutHandler

if TYPE_CHECKING: # Imports only for type annotations purposes (ignored at runtime)
  from PyQt5.QtWidgets import QApplication


class MusicCardWindow(QMainWindow):
  def __init__(self, app: "QApplication") -> None:
    super().__init__()
    self.set_showing_level()  # Set window flags and mainly "only desktop" or "always on top" mode
    self.setAttribute(Qt.WA_TranslucentBackground)

    self.screen: ScreenHandler = ScreenHandler(self, app)
    self.screen_geo = self.screen.get_screen_geometry(config.get_pr("screen_index"))
    self.setFixedSize(self.screen_geo.width(), self.screen_geo.height())
    self.move(self.screen_geo.x(), self.screen_geo.y())

    self.card: MusicCard = MusicCard(self)
    self.card.setParent(self)
    self.set_showing_mode()  # Set if the card should be "always on screen" or "hide dynamically"

    # Shortcut handler
    if config.get_pr("shortcuts"):
      self.shortcut = ShortcutHandler(self)

  def set_showing_level(self) -> None:
    if config.get_pr("only_on_desktop"):
      self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool)
    else:
      self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)

  def set_showing_mode(self) -> None:
    if config.get_pr("always_on_screen"):
      self.card.move(abs(config.get_pr("fixed_x_pos")), abs(config.get_pr("fixed_y_pos")))
    else:
      self.card.move(config.get_pr("start_x_pos"), config.get_pr("start_y_pos"))
