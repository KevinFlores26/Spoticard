import darkdetect
from PyQt5.QtCore import pyqtSignal, QObject, pyqtSlot
from abc import ABC, ABCMeta, abstractmethod
from typing import TYPE_CHECKING, Any, TypedDict, Callable
from config.config_main import config
from utils.helpers import set_timer

if TYPE_CHECKING: # Imports only for type annotations purposes (ignored at runtime)
  from PyQt5.QtCore import QTimer
  from ui.music_card.card import MusicCard
  from ui.music_card.animations import MusicCardAnimations
  from ui.music_card.handlers import UpdateHandler

QObjectMeta = type(QObject)


class MetaQObjectABC(QObjectMeta, ABCMeta):
  """
  Metaclass for the QObject class, in order to inherit from both ABC and QObject
  """
  pass


class IMetadataWorker(QObject, ABC, metaclass=MetaQObjectABC):
  """
  Gets the metadata from the current playback
  """
  getting: pyqtSignal = pyqtSignal()
  finished: pyqtSignal = pyqtSignal(object)

  def __init__(self):
    super().__init__()
    self.getting.connect(self.get_metadata)
    self.try_again_timer: "QTimer" = set_timer(self.get_metadata)
    self.tries: int = 0

  @abstractmethod
  def get_metadata(self) -> dict[str, Any]:
    pass

  def try_again(self, time: int) -> None:
    self.tries += 1
    self.try_again_timer.start(time)


class PlaybackInfoDict(TypedDict):
  current_track_id: str
  current_track: dict[str, Any]
  is_playing: bool
  previous_track_id: str
  previous_state_is_playing: bool
  shuffle_state: bool
  repeat_state: str
  volume_percent: int


class IMetadataHandler(ABC):
  """
  Handles the different scenarios where the metadata is
  correct, is not available or is wrong and calls the updater
  to update and show the card
  """

  def __init__(self, card: "MusicCard", updater: "UpdateHandler") -> None:
    super().__init__()
    self.card: "MusicCard" = card
    self.animations: "MusicCardAnimations" = self.card.animations
    self.updater: "UpdateHandler" = updater

    self.was_alert_card_shown: bool = False
    self.was_error_card_shown: bool = False

  @abstractmethod
  def handle_metadata(self, metadata: dict[str, Any]) -> None:
    pass

  @abstractmethod
  def show_info(self, metadata: dict[str, Any]) -> None:
    pass

  def show_theme_changed(self) -> None:
    if "adaptive" in config.current_theme_name:
      if config.is_os_dark != darkdetect.isDark():  # another 'if' because this would be called even if the theme is not adaptive
        config.switch_adaptive_theme()
        self.card.set_theme()
        self.animations.show_card()

    if config.is_changing_theme:
      self.card.set_theme()
      self.animations.show_card()
      config.is_changing_theme = False

  # Generic "show invalid info"
  def show_invalid_song_info(self, title: str, description: str, img_path: str = '', error: bool = False) -> None:
    img_path: str = r"resources\img\warning.png" if img_path == '' else img_path

    self.updater.update_card_content(title, description, img_path)

    if error:
      self.was_error_card_shown = True
    else:
      self.was_alert_card_shown = True
    self.card.playback_info["current_track_id"] = ''

  def requires_update(self) -> bool:
    # True if the song has changed
    if self.card.playback_info["previous_track_id"] != self.card.playback_info["current_track_id"]:
      return True

    # True if the song was paused and is now playing
    if not self.card.playback_info["previous_state_is_playing"] and self.card.playback_info["is_playing"]:
      return True

    return False


class IPlaybackWorker(QObject, ABC, metaclass=MetaQObjectABC):
  """
  Handles the events triggered by the shortcuts.
  These events can control the playback
  """
  on_playback_shortcut: pyqtSignal = pyqtSignal(str)

  def __init__(self, card: "MusicCard"):
    super().__init__()
    self.card: "MusicCard" = card

    self.volume: int = 0
    self.setting_volume: bool = False
    self.last_playback_order: int = 0

    self.shortcut_functions: dict[str, Callable] = {
      "play_pause": self.play_pause,
      "next": self.next_track,
      "previous": self.previous_track,
      "order": self.change_order,
      "repeat": self.toggle_repeat,
      "volume_up": lambda: self.change_volume(True),
      "volume_down": lambda: self.change_volume(False)
    }

    self.register_shortcuts()
    self.on_playback_shortcut.connect(self.execute_shortcut)

  @pyqtSlot(str)
  def execute_shortcut(self, shortcut: str) -> None:
    if self.card.is_snoozing:
      return

    self.shortcut_functions[shortcut]()

  @abstractmethod
  def register_shortcuts(self) -> None:
    pass

  @abstractmethod
  def play_pause(self) -> None:
    pass

  @abstractmethod
  def next_track(self) -> None:
    pass

  @abstractmethod
  def previous_track(self) -> None:
    pass

  @abstractmethod
  def change_order(self) -> None:
    pass

  @abstractmethod
  def toggle_repeat(self) -> None:
    pass

  @abstractmethod
  def change_volume(self, increase: bool) -> None:
    pass
