from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtWidgets import QMainWindow
from typing import TYPE_CHECKING

from config.config_main import config
from ui.music_card.card import MusicCard
from ui.music_card.handlers import ScreenHandler, ShortcutHandler

if TYPE_CHECKING: # Imports only for type annotations purposes (ignored at runtime)
  from PyQt5.QtWidgets import QApplication


class MusicCardWindow(QMainWindow):
  if config.get_pr("shortcuts"):
    # Receive signals from shortcuts
    visibility_listener: pyqtSignal = pyqtSignal()
    theme_listener: pyqtSignal = pyqtSignal()
    play_pause_listener: pyqtSignal = pyqtSignal()
    shuffle_listener: pyqtSignal = pyqtSignal()
    repeat_listener: pyqtSignal = pyqtSignal()
    next_listener: pyqtSignal = pyqtSignal()
    previous_listener: pyqtSignal = pyqtSignal()
    volume_up_listener: pyqtSignal = pyqtSignal()
    volume_down_listener: pyqtSignal = pyqtSignal()
    snooze_listener: pyqtSignal = pyqtSignal()
    exit_listener: pyqtSignal = pyqtSignal()

  def __init__(self, app: "QApplication") -> None:
    super().__init__()
    if config.get_pr("only_on_desktop"):
      self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool)
    else:
      self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
    self.setAttribute(Qt.WA_TranslucentBackground)

    self.screen: ScreenHandler = ScreenHandler(self, app)
    self.screen_geo = self.screen.get_screen_geometry(config.get_pr("screen_index"))
    self.setFixedSize(self.screen_geo.width(), self.screen_geo.height())
    self.move(self.screen_geo.x(), self.screen_geo.y())

    self.card: MusicCard = MusicCard(self)
    self.card.setParent(self)
    if config.get_pr("always_on_screen"):
      self.card.move(abs(config.get_pr("fixed_x_pos")), abs(config.get_pr("fixed_y_pos")))
    else:
      self.card.move(config.get_pr("start_x_pos"), config.get_pr("start_y_pos"))

    # Shortcut handlers
    self.shortcut = ShortcutHandler(self)
    self.visibility_listener.connect(self.shortcut.toggle_card_visibility)
    self.theme_listener.connect(self.shortcut.toggle_theme)
    self.play_pause_listener.connect(self.shortcut.toggle_playback)
    self.next_listener.connect(self.shortcut.next_track)
    self.previous_listener.connect(self.shortcut.previous_track)
    self.shuffle_listener.connect(self.shortcut.toggle_shuffle)
    self.repeat_listener.connect(self.shortcut.toggle_repeat)
    self.volume_up_listener.connect(self.shortcut.volume_up)
    self.volume_down_listener.connect(self.shortcut.volume_down)
    self.snooze_listener.connect(self.shortcut.toggle_snooze)
    self.exit_listener.connect(self.shortcut.exit_app)
