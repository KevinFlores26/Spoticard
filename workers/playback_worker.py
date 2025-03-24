from PyQt5 import QtCore
from PyQt5.QtCore import pyqtSignal
from utils.functions import debounce, get_current_playback

class FetchWorker(QtCore.QObject):
  fetching = pyqtSignal()
  finished = pyqtSignal(object)

  def __init__(self, sp, updater):
    super().__init__()
    self.sp = sp
    self.updater = updater
    self.fetching.connect(self.fetch)

  @QtCore.pyqtSlot()
  def fetch(self):
    print("Fetching...")
    current_playback = get_current_playback(self.sp)
    self.finished.emit(current_playback)


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
