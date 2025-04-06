import os, requests
from typing import TypedDict, Any, Callable
from media_players.base import IMetadataWorker, IMetadataHandler, IPlaybackWorker
from media_players.helpers.image_extractor import extract_embedded_image
from config.config_main import config


class MetadataDict(TypedDict):
  filepath: str
  title: str
  artist: str
  image: bytes | None
  is_playing: bool

class FB2KMetadataWorker(IMetadataWorker):
  def get_metadata(self) -> None:
    print(f"Fetching metadata...")

    if not os.path.exists(config.NOWPLAYING_TXT_PATH) and not config.NOWPLAYING_TXT_PATH.endswith(".txt"):
      self.finished.emit({ })
      return

    with open(config.NOWPLAYING_TXT_PATH, "r", encoding="utf-8") as file:
      lines = file.read().strip().split("\\n")

    # Sometimes the nowplaying text file can be empty (likely due to a bug from nowplaying fb2k component)
    if len(lines) == 1 and lines[0] == '' and config.is_nowplaying_txt_valid:
      return

    if len(lines) <= 3:
      self.finished.emit({ "case_error": "invalid_data" })
      return

    metadata: MetadataDict = {
      "filepath": lines[0],
      "title": lines[1],
      "artist": lines[2],
      "image": extract_embedded_image(filepath=lines[0]),
      "is_playing": True if lines[3] != '1' else False
    }

    if metadata["filepath"] == "":
      self.finished.emit({ "case_error": "invalid_data" })
      return

    # Fallback
    if not metadata["title"]:
      metadata["title"] = "<unknown>"
    if not metadata["artist"]:
      metadata["artist"] = "<unknown>"

    config.is_nowplaying_txt_valid = True  # The nowplaying text file is valid
    self.finished.emit(metadata)


class FB2KMetadataHandler(IMetadataHandler):
  @staticmethod
  def is_fb2k_standby(metadata: dict[str, Any]) -> bool:
    return metadata.get("title") == "?" and metadata.get("artist") == "?" and metadata.get("filepath") == "?"

  def handle_metadata(self, metadata: dict[str, Any]) -> None:
    if not isinstance(metadata, dict) and self.was_alert_card_shown:
      return

    if self.is_fb2k_standby(metadata) and not self.was_alert_card_shown:
      self.show_invalid_song_info("Not playing", "Turn on foobar2000 and play a great playlist")
      return

    if not metadata and not self.was_alert_card_shown:
      title: str = "Nowplaying text file not found"
      description: str = "Check if the file path is correct and if you have the corresponding foobar2000 component installed"

      self.show_invalid_song_info(title, description)
      return

    if metadata.get("case_error") == "invalid_data" and not self.was_error_card_shown:
      title: str = "Nowplaying text file is invalid"
      description: str = "Check if the components' params are correct. More info in the readme file"

      self.show_invalid_song_info(title, description, error=True)
      return

    if self.is_fb2k_standby(metadata) or not metadata or metadata.get("case_error"):
      return  # Not show the card until all is ok

    self.card.playback_info["current_track_id"] = metadata["filepath"]
    self.card.playback_info["current_track"] = metadata
    self.card.playback_info["is_playing"] = metadata["is_playing"]
    self.card.playback_info["shuffle_state"] = False
    self.card.playback_info["repeat_state"] = "off"
    self.card.playback_info["volume_percent"] = 0

    if self.requires_update():
      self.show_info(metadata)

    self.card.playback_info["previous_track_id"] = self.card.playback_info["current_track_id"]
    self.card.playback_info["previous_state_is_playing"] = self.card.playback_info["is_playing"]

  def show_info(self, metadata: dict[str, str | bytes | None]) -> None:
    title: str = metadata["title"]
    artist: str = metadata["artist"]
    image: str | bytes | None = metadata["image"]

    self.updater.update_card_content(title, artist, image)
    self.was_alert_card_shown = False
    self.was_error_card_shown = False


class FB2KPlaybackWorker(IPlaybackWorker):
  def send_command(self, cmd: str, param: str = "&param1=") -> None:
    """
    Sends a request to the http_control component server (must be installed).
    Only works with the default template (it comes with the component)
    :param cmd: playback command to execute
    :param param: (optional) some commands require parameters
    :return: None
    """
    COMMANDS: dict[str, str] = {
      "toggle_playback": "PlayOrPause",
      "next": "StartNext",
      "previous": "StartPrevious",
      "toggle_repeat": "ToggleRepeat",
      "order_playback": "PlaybackOrder",
      "change_volume": "Volume"
    }

    PARAMS: dict[str, str | int] = {
      "&param1=": "", # default param

      # repeat and playback order belongs to the same group of params (numbers from 0 to 6)
      "repeat_off": "",
      "repeat_playlist": 1,
      "repeat_track": 2,
      "order_default": 0,
      "order_random": 3,
      "order_shuffle_tracks": 4,
      "order_shuffle_albums": 5,
      "order_shuffle_folders": 6
    }

    if not cmd in COMMANDS:
      print("Command not found")
      return
    if not param in PARAMS:
      print("Parameter not found")
      return

    cmd = f"?cmd={COMMANDS[cmd]}"
    param = f"&param1={PARAMS[param]}"

    if cmd == "?cmd=ToggleRepeat" and param == "repeat_off":
      param = f"&param1={self.last_playback_order}" # repeat off does not exist in this API, so we use the last playback order

    endpoint: str = "http://127.0.0.1:8888/default/"
    url: str = endpoint + cmd + param
    request: requests.Response = requests.get(url)

    if request.status_code != 200:
      print("Failed to send command.")
      return

    if cmd == "?cmd=PlaybackOrder" and param != "&param1=":
      self.last_playback_order = PARAMS[param] # save the last playback order

    print("Command sent successfully.")

  def toggle_playback(self) -> None:
    self.send_command("toggle_playback")

  def next_track(self) -> None:
    self.send_command("next")

  def previous_track(self) -> None:
    self.send_command("previous")

  # TODO: implement logic when I found a way to get proper (not using the text file)
  def toggle_repeat(self) -> None:
    pass

  def order_playback(self) -> None:
    pass

  def change_volume(self, increase: bool) -> None:
    pass
