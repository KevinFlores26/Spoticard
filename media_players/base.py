from PyQt5 import QtCore
from PyQt5.QtCore import pyqtSignal
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, TypedDict
from utils.functions import get_pr, convert_img_to_pixmap

if TYPE_CHECKING: # Imports only for type annotations purposes (ignored at runtime)
  from PyQt5 import QtGui
  from ui.music_card.music_card_main import MusicCard
  from ui.music_card.animations import MusicCardAnimations
  from ui.music_card.handlers import UpdateHandler

class IMetadataWorker(ABC):
  """
  Gets the metadata from the current playback
  """
  getting: QtCore.pyqtSignal = pyqtSignal(str)
  finished: QtCore.pyqtSignal = pyqtSignal(dict[str, Any])

  def __init__(self):
    self.getting.connect(self.get_metadata)

  @abstractmethod
  def get_metadata(self) -> dict[str, Any]:
    pass


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
  def __init__(self, card: MusicCard):
    super().__init__()
    self.card: MusicCard = card
    self.animations: MusicCardAnimations = self.card.animations
    self.updater: UpdateHandler = self.card.updater

    self._playback_info: PlaybackInfoDict = {
      "current_track_id": '',
      "current_track": { },
      "is_playing": False,
      "previous_track_id": '',
      "previous_state_is_playing": False,
      "shuffle_state": False,
      "repeat_state": "off",
      "volume_percent": 0
    }

    self.was_alert_card_shown: bool = False
    self.was_error_card_shown: bool = False

  @property
  def playback_info(self) -> PlaybackInfoDict:
    return self._playback_info

  @abstractmethod
  def handle_metadata(self, metadata: dict[str, Any]) -> None:
    pass

  @abstractmethod
  def show_info(self, metadata: dict[str, Any]) -> None:
    pass

  # Generic "show invalid info"
  def show_invalid_song_info(self, title: str, description: str, img_path: str = '') -> None:
    img_path: str = r"resources\img\warning.png" if img_path == '' else img_path
    pixmap: QtGui.QPixmap = convert_img_to_pixmap(get_pr("image_size"), img_path, False)

    self.updater.update_card_properties(current_track=None, title=title, artist=description, pixmap=pixmap)
    self.was_alert_card_shown = True
    self._playback_info["previous_track_id"] = ''

  def requires_update(self) -> bool:
    # True if the song has changed
    if self._playback_info["previous_track_id"] != self._playback_info["current_track_id"]:
      return True

    # True if the song was paused and is now playing
    if not self._playback_info["previous_state_is_playing"] and self._playback_info["is_playing"]:
      return True

    return False


class IPlaybackWorker(ABC):
  """
  Handles the events triggered by the shortcuts.
  These events can control the playback
  """
  on_toggle_playback: QtCore.pyqtSignal = pyqtSignal()
  on_next_track: QtCore.pyqtSignal = pyqtSignal()
  on_previous_track: QtCore.pyqtSignal = pyqtSignal()
  on_order_playback: QtCore.pyqtSignal = pyqtSignal()
  on_repeat: QtCore.pyqtSignal = pyqtSignal()
  on_volume: QtCore.pyqtSignal = pyqtSignal(bool)

  def __init__(self, metadata_handler: IMetadataHandler):
    super().__init__()
    self.metadata_handler: IMetadataHandler = metadata_handler
    self.volume: int = 0
    self.setting_volume: bool = False

    self.on_toggle_playback.connect(self.toggle_playback)
    self.on_next_track.connect(self.next_track)
    self.on_previous_track.connect(self.previous_track)
    self.on_order_playback.connect(self.order_playback)
    self.on_repeat.connect(self.toggle_repeat)
    self.on_volume.connect(self.change_volume)

  @QtCore.pyqtSlot()
  @abstractmethod
  def toggle_playback(self) -> None:
    pass

  @QtCore.pyqtSlot()
  @abstractmethod
  def next_track(self) -> None:
    pass

  @QtCore.pyqtSlot()
  @abstractmethod
  def previous_track(self) -> None:
    pass

  @QtCore.pyqtSlot()
  @abstractmethod
  def order_playback(self) -> None:
    pass

  @QtCore.pyqtSlot()
  @abstractmethod
  def toggle_repeat(self) -> None:
    pass

  @QtCore.pyqtSlot(bool)
  @abstractmethod
  def change_volume(self, increase: bool) -> None:
    pass
