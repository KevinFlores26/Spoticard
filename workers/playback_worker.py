import os
from PyQt5 import QtCore
from PyQt5.QtCore import pyqtSignal
from mutagen.mp3 import MP3
from mutagen.flac import FLAC
from mutagen.mp4 import MP4
from mutagen.id3 import ID3, APIC
from utils.functions import debounce, get_current_playback
from config.config import NOWPLAYING_TXT_PATH


class MetadataWorker(QtCore.QObject):
  fetching: QtCore.pyqtSignal = pyqtSignal(str)
  finished: QtCore.pyqtSignal = pyqtSignal(object)

  def __init__(self, sp=None):
    super().__init__()
    self.sp = sp  # Spotipy instance
    self.fetching.connect(self.fetch)

  @QtCore.pyqtSlot(str)
  def fetch(self, player):
    print(f"Fetching metadata from {player}...")

    if player == "spotify":
      current_playback = get_current_playback(self.sp)
    elif player == "foobar2000":
      current_playback = self.get_now_playing_from_txt()
    else:
      current_playback = None

    self.finished.emit(current_playback)

  def get_now_playing_from_txt(self):
    if not os.path.exists(NOWPLAYING_TXT_PATH):
      return None

    with open(NOWPLAYING_TXT_PATH, "r", encoding="utf-8") as file:
      lines = file.read().strip().split("\\n")

    if len(lines) != 4:
      return None  # Invalid data

    img = self.extract_embedded_art(lines[2])
    return {
      "title": lines[0],
      "artist": lines[1],
      "filepath": lines[2],
      "is_playing": True if lines[3] != '1' else False,
      "img_bytes": img
    }

  @staticmethod
  def extract_embedded_art(filepath):
    audio = None
    art = None

    if filepath.endswith(".mp3"):
      audio = MP3(filepath, ID3=ID3)
      for tag in audio.tags.values():
        if isinstance(tag, APIC):
          art = tag.data
          break

    elif filepath.endswith(".flac"):
      audio = FLAC(filepath)
      if audio.pictures:
        art = audio.pictures[0].data

    elif filepath.endswith(".m4a") or filepath.endswith(".mp4"):
      audio = MP4(filepath)
      if "covr" in audio.tags:
        art = audio.tags["covr"][0]

    return art


class PlayerWorker(QtCore.QObject):
  on_toggle_playback = pyqtSignal()
  on_next_track = pyqtSignal()
  on_previous_track = pyqtSignal()
  on_shuffle = pyqtSignal()
  on_repeat = pyqtSignal()
  on_volume = pyqtSignal(bool)

  def __init__(self, sp=None):
    super().__init__()
    self.sp = sp
    self.volume = 0
    self.setting_volume = False

    self.on_toggle_playback.connect(self.toggle_playback)
    self.on_next_track.connect(self.next_track)
    self.on_previous_track.connect(self.previous_track)
    self.on_shuffle.connect(self.toggle_shuffle)
    self.on_repeat.connect(self.toggle_repeat)
    self.on_volume.connect(self.change_volume)

  @QtCore.pyqtSlot()
  def toggle_playback(self):
    current_playback = get_current_playback(self.sp)
    if current_playback and current_playback['is_playing']:
      self.sp.pause_playback()
    elif current_playback and not current_playback['is_playing']:
      self.sp.start_playback()

  @QtCore.pyqtSlot()
  def next_track(self):
    self.sp.next_track()

  @QtCore.pyqtSlot()
  def previous_track(self):
    self.sp.previous_track()

  @QtCore.pyqtSlot()
  def toggle_shuffle(self):
    current_playback = get_current_playback(self.sp)
    if current_playback['shuffle_state'] is True:
      self.sp.shuffle(False)
      print("shuffle turned off")
    else:
      self.sp.shuffle(True)
      print("shuffle turned on")

  @QtCore.pyqtSlot()
  def toggle_repeat(self):
    REPEAT_MODES = ['off', 'context', 'track']
    current_playback = get_current_playback(self.sp)

    index = REPEAT_MODES.index(current_playback['repeat_state'])
    for mode in REPEAT_MODES:
      if mode != REPEAT_MODES[index]: continue

      next_mode = REPEAT_MODES[(index + 1) % len(REPEAT_MODES)]
      self.sp.repeat(next_mode)
      print(f"Set repeat mode to: {next_mode}")
      return

    self.sp.repeat(REPEAT_MODES[0])
    print(f"Set repeat mode to: {REPEAT_MODES[0]}")

  @debounce(1000)
  def set_volume(self):
    self.sp.volume(self.volume)
    print(f"Volume set to: {self.volume}%")

    self.volume = 0
    self.setting_volume = False

  @QtCore.pyqtSlot(bool)
  def change_volume(self, up):

    current_playback = get_current_playback(self.sp)
    current_volume = current_playback['device']['volume_percent']
    if not self.setting_volume:
      self.setting_volume = True
      self.volume = current_volume

    if up:
      if self.volume == 100:
        print("Volume is already at 100%")
        return

      self.volume = round(min(100, self.volume + 10), -1)
      print(self.volume)
    else:
      if self.volume == 0:
        print("Volume is already at 0%")
        return

      self.volume = round(max(0, self.volume - 10), -1)
      print(self.volume)

    self.set_volume()
