import requests, time
from PyQt5 import QtCore
from PyQt5.QtCore import pyqtSignal, QThread


class PlayerWorker(QtCore.QObject):
  on_toggle_playback = pyqtSignal()
  on_next_track = pyqtSignal()
  on_previous_track = pyqtSignal()
  on_shuffle = pyqtSignal()
  on_repeat = pyqtSignal()
  on_volume_up = pyqtSignal()
  on_volume_down = pyqtSignal()

  def __init__(self, sp=None):
    super().__init__()
    self.sp = sp
    self.current_volume = None

    self.on_toggle_playback.connect(self.toggle_playback)
    self.on_next_track.connect(self.next_track)
    self.on_previous_track.connect(self.previous_track)
    self.on_shuffle.connect(self.toggle_shuffle)
    self.on_repeat.connect(self.toggle_repeat)
    self.on_volume_up.connect(self.volume_up)
    self.on_volume_down.connect(self.volume_down)

  @QtCore.pyqtSlot()
  def get_current_playback(self, retries=3, delay=5):
    # Gets the current playback information and retry if it fails
    for attempt in range(retries):
      try:
        current_playback = self.sp.current_playback()
        return current_playback
      except requests.exceptions.ReadTimeout:
        print(f"ReadTimeout error. Retry {attempt + 1} of {retries} in {delay} seconds...")
        time.sleep(delay)
      except requests.exceptions.RequestException as e:
        print(f"Other request error: {e}")
        return None

    return None

  @QtCore.pyqtSlot()
  def toggle_playback(self):
    current_playback = self.get_current_playback()
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
    current_playback = self.get_current_playback()
    if current_playback['shuffle_state'] is True:
      self.sp.shuffle(False)
      print("shuffle turned off")
    else:
      self.sp.shuffle(True)
      print("shuffle turned on")

  @QtCore.pyqtSlot()
  def toggle_repeat(self):
    REPEAT_MODES = ['off', 'context', 'track']
    current_playback = self.get_current_playback()

    index = REPEAT_MODES.index(current_playback['repeat_state'])
    for mode in REPEAT_MODES:
      if mode != REPEAT_MODES[index]: continue

      next_mode = REPEAT_MODES[(index + 1) % len(REPEAT_MODES)]
      self.sp.repeat(next_mode)
      print(f"Set repeat mode to: {next_mode}")
      return

    self.sp.repeat(REPEAT_MODES[0])
    print(f"Set repeat mode to: {REPEAT_MODES[0]}")

  @QtCore.pyqtSlot()
  def volume_up(self):
    current_playback = self.get_current_playback()
    current_volume = current_playback['device']['volume_percent']
    if current_volume == 100:
      print("Volume is already at 100%")
      return

    new_volume = min(100, current_volume + 10)
    self.sp.volume(new_volume)
    print(f"Set volume to: {new_volume}%")

  @QtCore.pyqtSlot()
  def volume_down(self):
    current_playback = self.get_current_playback()
    current_volume = current_playback['device']['volume_percent']
    if current_volume == 0:
      print("Volume is already at 0%")
      return

    new_volume = max(0, current_volume - 10)
    self.sp.volume(new_volume)
    print(f"Set volume to: {new_volume}%")
