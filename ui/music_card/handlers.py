from PyQt5.QtCore import QTimer, QThread
from PyQt5.QtGui import QCursor
from PyQt5.QtWidgets import QApplication
from typing import TYPE_CHECKING, Any, Union

from config.config_main import config
from utils.helpers import set_timer
from utils.image_handling import ConvertImageToPixmap, ExtractImageColor
from media_players.factory import get_factory

if TYPE_CHECKING:  # Imports only for type annotations purposes (ignored at runtime)
  from PyQt5.QtCore import QRect, QPoint
  from PyQt5.QtGui import QPixmap, QScreen
  from media_players.factory import IMediaPlayerFactory
  from media_players.base import IMetadataWorker, IMetadataHandler, IPlaybackWorker
  from ui.music_card.window import MusicCardWindow
  from ui.music_card.card import MusicCard
  from ui.music_card.animations import MusicCardAnimations

PLAYER = config.get_pr("media_player")
MEDIA_FACTORY: "IMediaPlayerFactory" = get_factory(PLAYER)

class UpdateHandler:
  def __init__(self, card: "MusicCard"):
    self.card: "MusicCard" = card
    self.animations: "MusicCardAnimations" = card.animations

    self.loop_timer: QTimer = set_timer(self.start_loop)
    self.metadata_handler: "IMetadataHandler" = MEDIA_FACTORY.create_metadata_handler(self.card, self)

    self.worker: "IMetadataWorker" = MEDIA_FACTORY.create_metadata_worker()
    self.thread: QThread = QThread()
    self.worker.moveToThread(self.thread)
    self.worker.finished.connect(self.update_card)
    self.thread.start()

  # The loop: start_loop -> MetadataWorker -> update_card -> start again
  def start_loop(self) -> None:
    if self.loop_timer.isActive():
      self.loop_timer.stop()

    # Not update the card when it is snoozing or when it is on the screen (excluding when always_on_screen is on)
    if self.card.is_snoozing:
      return

    elif not config.get_pr("always_on_screen") and self.card.is_card_showing:
      self.loop_timer.start(1000)
      return

    self.worker.getting.emit()

  def update_card(self, current_playback: dict[str, Any]):
    self.metadata_handler.show_theme_changed()  # Shows the card if the theme has changed
    self.metadata_handler.handle_metadata(current_playback)  # Shows the card based on rules set by the current media player

    self.loop_timer.start(1000)  # Loop starts again

  # Card Content Handling
  def update_card_content(
    self,
    title: str,
    artist: str,
    img_src: str | bytes | None = None,
    bar_color: str = config.get_pr("custom_color")
  ) -> None:
    self.reset_card_content()

    image_color: str = bar_color
    i_converter: ConvertImageToPixmap = ConvertImageToPixmap()
    i_extractor: ExtractImageColor = ExtractImageColor()

    if not img_src:
      img_src = r"resources\img\warning.png"  # TODO: Replace with a default image

    pixmap: Union["QPixmap", None] = i_converter.convert(img_src, config.get_pr("image_size"), config.get_pr("image_radius"))
    if not config.get_pr("only_custom_color"):
      image_color = i_extractor.extract(img_src, config.current_theme.get("bg_color"))

    # Set properties
    self.card.title_label.setText(title)
    self.card.artist_label.setText(artist)
    self.card.set_pixmap(self.card, pixmap)
    self.card.bar.setStyleSheet(f"background-color: {image_color};")

    # Set the card width manually
    total_width: int = self.card.get_total_width(self.card.main_layout, config.get_pr("card_spacing"), config.get_pr("min_card_width"))
    self.card.setFixedWidth(total_width)

    # Update valid card's coordinates
    rect: "QRect" = self.card.geometry()
    coords: dict[str, tuple[int, int]] = {
      "upper_left": (config.get_pr("end_x_pos"), config.get_pr("end_y_pos")),
      "upper_right": (config.get_pr("end_x_pos") + rect.width(), config.get_pr("end_y_pos")),
      "lower_left": (config.get_pr("end_x_pos"), config.get_pr("end_y_pos") + rect.height()),
      "lower_right": (config.get_pr("end_x_pos") + rect.width(), config.get_pr("end_y_pos") + rect.height()),
    }
    self.card.coords = coords
    self.animations.show_card()

  def reset_card_content(self):
    if self.card.opacity_effect.opacity() == 0:
      self.animations.fade_in()

    self.card.bar.setStyleSheet(f"background-color: {config.get_pr('custom_accent')};")
    self.card.title_label.setText("")
    self.card.artist_label.setText("")
    self.card.img_label.clear()


class CursorHandler:
  def __init__(self, card: "MusicCard") -> None:
    self.card: "MusicCard" = card
    self.animations: "MusicCardAnimations" = self.card.animations
    self.hover_timer: QTimer = set_timer(self.card.call_leave_event)

  def on_click(self) -> None:
    if self.card.is_faded_out:
      return

    self.card.is_faded_out = True
    self.animations.fade_out()

  def on_leave(self, force_show: bool = False) -> None:
    if not self.card.is_faded_out:
      self.hover_timer.stop()
      return

    if force_show:
      self.card.is_faded_out = False
      self.animations.fade_in()
      return

    c_pos: "QPoint" = QCursor.pos()  # cursor position
    u_left: tuple[int, int] = self.card.coords["upper_left"]
    l_right: tuple[int, int] = self.card.coords["lower_right"]

    # Check if the card left the screen
    if (
      c_pos.x() < u_left[0] or
      c_pos.y() < u_left[1] or
      c_pos.x() > l_right[0] or
      c_pos.y() > l_right[1]
    ):
      self.card.is_faded_out = False
      self.animations.fade_in()
    else:
      self.hover_timer.start(100)


class ShortcutHandler:
  def __init__(self, window: "MusicCardWindow") -> None:
    self.window: "MusicCardWindow" = window
    self.card: "MusicCard" = self.window.card
    self.animations: "MusicCardAnimations" = self.card.animations
    self.closing_timer: QTimer = set_timer(self.exit_app)

    self.thread: QThread = QThread()
    self.worker: "IPlaybackWorker" = MEDIA_FACTORY.create_playback_worker(self.card)
    self.worker.moveToThread(self.thread)
    self.thread.start()

  # App related shortcuts
  def toggle_snooze(self) -> None:
    if self.card.is_snoozing:
      print("Awake...")
      if self.card.is_card_showing:
        self.animations.fade_in()

      self.card.is_snoozing = False
      self.card.updater.start_loop()

    else:
      print("Snoozing...")
      if self.card.is_card_showing:
        self.animations.fade_out()

      self.card.is_snoozing = True

  def exit_app(self) -> None:
    print("Exiting...")
    if self.card.is_card_showing:
      self.animations.fade_out()

    QTimer.singleShot(500, lambda: QApplication.quit())

  # Visual related shortcuts
  def toggle_card_visibility(self) -> None:
    if self.card.is_snoozing:
      return

    if not self.card.is_card_showing:
      self.animations.show_card()
    elif not self.card.is_faded_out and self.card.is_card_showing:
      self.card.cursor_handler.on_click()
    elif self.card.is_faded_out:
      self.card.cursor_handler.on_leave(True)

  def toggle_theme(self) -> None:
    if self.card.is_snoozing:
      return

    next_theme_name: str = next(config.themes_cycle)
    print(f"{next_theme_name=}")
    config.set_current_theme(next_theme_name)

  # Player related shortcuts
  def toggle_playback(self) -> None:
    if not self.card.is_snoozing:
      self.worker.on_toggle_playback.emit()

  def next_track(self) -> None:
    if not self.card.is_snoozing:
      self.worker.on_next_track.emit()

  def previous_track(self) -> None:
    if not self.card.is_snoozing:
      self.worker.on_previous_track.emit()

  def toggle_shuffle(self) -> None:
    if not self.card.is_snoozing:
      self.worker.on_order_playback.emit()

  def toggle_repeat(self) -> None:
    if not self.card.is_snoozing:
      self.worker.on_repeat.emit()

  def volume_up(self) -> None:
    if not self.card.is_snoozing:
      self.worker.on_volume.emit(True)

  def volume_down(self) -> None:
    if not self.card.is_snoozing:
      self.worker.on_volume.emit(False)


class ScreenHandler:
  def __init__(self, window: "MusicCardWindow", app: QApplication) -> None:
    self.window: "MusicCardWindow" = window
    self.screens: list["QScreen"] = app.screens()

  def get_screen_geometry(self, screen_index: int = 0) -> "QRect":
    index: int = self.verify_screen_index(screen_index)
    screen: "QScreen" = self.screens[index]
    screen_geometry: "QRect" = screen.geometry()

    return screen_geometry

  def verify_screen_index(self, screen_index: int = 0) -> int:
    if screen_index > (len(self.screens) - 1):
      return len(self.screens) - 1
    elif screen_index < 0:
      return 0

    return screen_index
