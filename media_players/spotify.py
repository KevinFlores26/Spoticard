import requests, time
from typing import Any, TYPE_CHECKING
from media_players.base import IMetadataWorker, IMetadataHandler, IPlaybackWorker
from config.config import SP
from utils.functions import debounce

if TYPE_CHECKING: # Imports only for type annotations purposes (ignored at runtime)
  from media_players.base import PlaybackInfoDict

class SpotifyMetadataWorker(IMetadataWorker):
  def get_metadata(self) -> None:
    print(f"Fetching metadata...")
    current_playback: dict[str, Any] = { }
    retries: int = 3
    delay: int = 5

    for attempt in range(retries):
      try:
        current_playback = SP.current_playback()

      except requests.exceptions.ReadTimeout:
        print(f"ReadTimeout error. Retry {attempt + 1} of {retries} in {delay} seconds...")
        time.sleep(delay)

      except requests.exceptions.RequestException as e:
        print(f"Other request error: {e}")

    self.finished.emit(current_playback)


class SpotifyMetadataHandler(IMetadataHandler):
  def handle_metadata(self, metadata: dict[str, Any]) -> None:
    if not metadata and not self.was_alert_card_shown:
      self.show_invalid_song_info("Not playing", "Turn on Spotify or check your internet connection")
      return

    elif metadata.get("currently_playing_type") == "ad" and not self.was_alert_card_shown:
      self.show_invalid_song_info("Spotify ad", "Please wait until the ad is over")
      return

    elif not metadata.get("item") and not self.was_alert_card_shown:
      self.show_invalid_song_info("No Title", "No Artist")
      return

    playback_item: dict[str, Any] = metadata.get("item")

    # Update current info
    self._playback_info["current_track_id"] = playback_item.get("id")
    self._playback_info["current_track"] = playback_item
    self._playback_info["is_playing"] = metadata.get("is_playing")
    self._playback_info["shuffle_state"] = metadata.get("shuffle_state")
    self._playback_info["repeat_state"] = metadata.get("repeat_state")
    self._playback_info["volume_percent"] = metadata.get("device").get("volume_percent")

    if self.requires_update():
      self.show_info(metadata)

    # Update previous info (really the same as the current one, but for comparison purposes)
    self._playback_info["previous_track_id"] = self._playback_info["current_track_id"]
    self._playback_info["previous_state_is_playing"] = self._playback_info["is_playing"]


  def show_info(self, metadata: dict[str, Any]) -> None:
    current_playback: dict[str, Any] = metadata.get("item", { })

    # If the method was called without handling the metadata first
    if not current_playback:
      self.handle_metadata(metadata)
      return

    title: str = current_playback.get("name")
    artist: str = current_playback.get("artists")[0].get("name")
    img_url: str = current_playback.get("album").get("images")[0].get("url")

    self.updater.update_card_properties(None, title, artist, img_url)
    self.was_alert_card_shown = False


class SpotifyPlaybackWorker(IPlaybackWorker):
  def toggle_playback(self) -> None:
    current_playback: PlaybackInfoDict = self.metadata_handler.playback_info
    if not current_playback:
      return

    if current_playback.get("is_playing"):
      SP.pause_playback()
    elif not current_playback.get("is_playing"):
      SP.start_playback()

  def next_track(self) -> None:
    SP.next_track()

  def previous_track(self) -> None:
    SP.previous_track()

  def order_playback(self) -> None:
    current_playback: PlaybackInfoDict = self.metadata_handler.playback_info

    if current_playback.get("shuffle_state"):
      SP.shuffle(False)
      print("shuffle turned off")
    else:
      SP.shuffle(True)
      print("shuffle turned on")

  def toggle_repeat(self) -> None:
    REPEAT_MODES: list[str] = ['off', 'context', 'track']
    current_playback: PlaybackInfoDict = self.metadata_handler.playback_info

    index = REPEAT_MODES.index(current_playback.get('repeat_state', REPEAT_MODES[0]))
    for mode in REPEAT_MODES:
      if mode != REPEAT_MODES[index]:
        continue

      next_mode = REPEAT_MODES[(index + 1) % len(REPEAT_MODES)]
      SP.repeat(next_mode)
      print(f"Set repeat mode to: {next_mode}")

  @debounce(1000)
  def set_volume(self) -> None:
    SP.volume(self.volume)
    print(f"Volume set to: {self.volume}%")

    self.volume = 0
    self.setting_volume = False

  def change_volume(self, increase: bool) -> None:
    current_playback: PlaybackInfoDict = self.metadata_handler.playback_info
    current_volume: int = current_playback['volume_percent']

    if not self.setting_volume:
      self.setting_volume = True
      self.volume = current_volume

    if increase:
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
