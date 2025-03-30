from PyQt5 import QtGui, QtWidgets, QtCore
from PyQt5.QtCore import QTimer
from config.config_main import config
from utils.functions import get_image_color, get_total_width, convert_img_to_pixmap, set_timer, set_theme, set_pixmap, assign_metadata
from utils.helpers import THEME_NAMES
from workers.playback_worker import PlayerWorker, MetadataWorker

PLAYER = config.get_pr("player")

class UpdateHandler:
  def __init__(self, card):
    self.card = card
    self.animations = self.card.animations

    self.current_track = None
    self.current_track_id = None
    self.is_playing = None
    self.previous_track_id = None
    self.previous_is_playing = None

    self.alert_card_shown = False
    self.loop_timer = set_timer(self.start_loop)

    self.worker = MetadataWorker()

    self.thread = QtCore.QThread()
    self.worker.moveToThread(self.thread)
    self.worker.finished.connect(self.update_card)
    self.thread.start()

  # The loop: start_loop -> FetchWorker -> update_card -> start again
  def start_loop(self):
    if self.loop_timer.isActive():
      self.loop_timer.stop()

    # Not update the card when it is snoozing or when it is on the screen (excluding when always_on_screen is on)
    if (not config.get_pr("always_on_screen") and self.card.showing_card) or self.card.is_snoozing:
      return

    self.worker.fetching.emit(PLAYER)

  def update_card(self, current_playback):
    current_playback = assign_metadata(current_playback, PLAYER)

    # Set theme if it was changed and show the card
    if self.card.current_theme.get("THEME_NAME") != config.current_theme.get("THEME_NAME"):
      self.show_theme_changed(config.current_theme, current_playback)

    # Show warning card if Spotify is not connected
    elif PLAYER == "spotify" and not current_playback and not self.alert_card_shown:
      self.show_spotify_not_connected()

    # Show the card when the current track has not valid information
    elif PLAYER == "spotify" and current_playback and current_playback.get("case") and not self.alert_card_shown:
      if current_playback.get("case") == "ad":
        self.show_invalid_song_info("Spotify ad", "Please wait until the ad is over")
      if current_playback.get("case") == "no_track_info":
        self.show_invalid_song_info("No Title", "No Artist")

    # Show the card with the current track (normal case)
    elif current_playback and len(current_playback) >= 5:  # At least artist, title, album, img reference and is_playing
      self.show_normal_case(current_playback)

    self.loop_timer.start(1000)  # Loop starts again

  # SHOW THE CARD CASES
  def show_theme_changed(self, theme, current_playback):
    card_labels = [self.card.title_label, self.card.artist_label]
    set_theme(self.card, card_labels, theme)
    self.card.current_theme = theme

    self.update_card_properties(current_playback)

  def show_spotify_not_connected(self):
    title = "Not playing"
    artist = "Turn on Spotify or check your internet connection"
    pixmap = convert_img_to_pixmap(config.get_pr("image_size"), r"resources\img\warning.png", False)

    # Set properties
    self.update_card_properties(None, title, artist, pixmap)
    self.alert_card_shown = True
    self.previous_track_id = None

  def show_invalid_song_info(self, title, description):
    pixmap = convert_img_to_pixmap(config.get_pr("image_size"), r"resources\img\warning.png", False)
    self.update_card_properties(current_track=None, title=title, artist=description, pixmap=pixmap)
    self.alert_card_shown = True
    self.previous_track_id = None

  def show_normal_case(self, current_playback):
    self.alert_card_shown = False
    self.current_track = current_playback
    self.is_playing = current_playback.get("is_playing")

    if PLAYER == "spotify":
      self.current_track_id = self.current_track.get("id", 1)
    elif PLAYER == "foobar2000":
      self.current_track_id = self.current_track.get("filepath")

    # Shows the card if the song changes, or it changes its state (pause to playing)
    if self.current_track_id != self.previous_track_id or self.previous_is_playing == False and self.is_playing == True:
      self.update_card_properties(self.current_track)

    # Update the previous state
    self.previous_track_id = self.current_track_id
    self.previous_is_playing = self.is_playing

  # Helpers
  def update_card_properties(
    self,
    current_track,
    title="No Title",
    artist="No Artist",
    pixmap=None,
    image_color=config.get_pr("custom_color"),
  ):
    self.reset_card_properties()

    if current_track:
      title = current_track.get("title")
      artist = current_track.get("artist")

      # Get and show the song's image
      img_src = current_track.get("img_url")
      is_remote = True

      if not img_src and current_track.get("filepath"):
        img_src = current_track.get("img_bytes")  # image embedded from the track

      if not img_src:
        img_src = r"resources\img\warning.png"
        is_remote = False

      pixmap = convert_img_to_pixmap(config.get_pr("image_size"), img_src, is_remote, config.get_pr("image_radius"))

      if not config.get_pr("only_custom_color") and is_remote == False:
        image_color = get_image_color(img_src, self.card.current_theme.get("bg_color"), config.get_pr("dominant_color"), False)
      else:
        image_color = get_image_color(img_src, self.card.current_theme.get("bg_color"), config.get_pr("dominant_color"))

    # Set properties
    self.card.title_label.setText(title)
    self.card.artist_label.setText(artist)
    set_pixmap(self.card, pixmap)
    self.card.bar.setStyleSheet(f"background-color: {image_color};")

    # Set the card width manually
    total_width = get_total_width(self.card.card_layout, config.get_pr("card_spacing"), config.get_pr("min_card_width"))
    self.card.setFixedWidth(total_width)

    # Update valid card's coordinates
    rect = self.card.geometry()
    coords = {
      "upper_left": [config.get_pr("end_x_pos"), config.get_pr("end_y_pos")],
      "upper_right": [config.get_pr("end_x_pos") + rect.width(), config.get_pr("end_y_pos")],
      "lower_left": [config.get_pr("end_x_pos"), config.get_pr("end_y_pos") + rect.height()],
      "lower_right": [config.get_pr("end_x_pos") + rect.width(), config.get_pr("end_y_pos") + rect.height()],
    }
    self.card.coords = coords
    self.animations.show_card()

  def reset_card_properties(self):
    if self.card.opacity_effect.opacity() == 0:
      self.animations.fade_in()

    self.card.bar.setStyleSheet(f"background-color: {config.get_pr('custom_accent')};")
    self.card.title_label.setText("")
    self.card.artist_label.setText("")
    self.card.img_label.clear()


class CursorHandler:
  def __init__(self, card):
    self.card = card
    self.animations = self.card.animations
    self.hover_timer = set_timer(self.card.call_leave_event)

  def on_click(self):
    if self.card.is_faded_out:
      return

    self.card.is_faded_out = True
    self.animations.fade_out()

  def on_leave(self, force_show=False):
    if not self.card.is_faded_out:
      self.hover_timer.stop()
      return

    if force_show:
      self.card.is_faded_out = False
      self.animations.fade_in()
      return

    c_pos = QtGui.QCursor.pos()  # cursor position
    u_left = self.card.coords["upper_left"]
    l_right = self.card.coords["lower_right"]

    # Check if the card left the screen
    if (
      c_pos.x() < u_left[0]
      or c_pos.y() < u_left[1]
      or c_pos.x() > l_right[0]
      or c_pos.y() > l_right[1]
    ):
      self.card.is_faded_out = False
      self.animations.fade_in()
    else:
      self.hover_timer.start(100)


class ShortcutHandler:
  def __init__(self, window):
    self.window = window
    self.card = self.window.card
    self.animations = self.card.animations
    self.closing_timer = set_timer(self.exit_app)

    self.thread = QtCore.QThread()
    self.worker = PlayerWorker()
    self.worker.moveToThread(self.thread)
    self.thread.start()

  # App related shortcuts
  def toggle_snooze(self):
    if self.card.is_snoozing:
      print("Awake...")
      if self.card.showing_card: self.animations.fade_in()
      self.card.is_snoozing = False
      self.card.updater.start_loop()
    else:
      print("Snoozing...")
      if self.card.showing_card: self.animations.fade_out()
      self.card.is_snoozing = True

  def exit_app(self):
    print("Exiting...")
    if self.card.showing_card: self.animations.fade_out()
    QTimer.singleShot(500, lambda: QtWidgets.QApplication.quit())

  # Visual related shortcuts
  def toggle_card_visibility(self):
    if self.card.is_snoozing: return

    if not self.card.showing_card:
      self.animations.show_card()
    elif not self.card.is_faded_out and self.card.showing_card:
      self.card.cursor_handler.on_click()
    elif self.card.is_faded_out:
      self.card.cursor_handler.on_leave(True)

  def toggle_theme(self):
    if self.card.is_snoozing: return

    index = THEME_NAMES.index(self.card.theme_name)
    for name in THEME_NAMES:
      if name != THEME_NAMES[index]: continue

      next_theme_name = THEME_NAMES[(index + 1) % len(THEME_NAMES)]
      print(f"Set theme to: {next_theme_name}")
      self.card.theme_name = next_theme_name
      return

    print(f"Set theme to: {THEME_NAMES[0]}")
    self.card.theme_name = THEME_NAMES[0]

  # Player related shortcuts
  def toggle_playback(self):
    if not self.card.is_snoozing:
      self.worker.on_toggle_playback.emit()

  def next_track(self):
    if not self.card.is_snoozing:
      self.worker.on_next_track.emit()

  def previous_track(self):
    if not self.card.is_snoozing:
      self.worker.on_previous_track.emit()

  def toggle_shuffle(self):
    if not self.card.is_snoozing:
      self.worker.on_shuffle.emit()

  def toggle_repeat(self):
    if not self.card.is_snoozing:
      self.worker.on_repeat.emit()

  def volume_up(self):
    if not self.card.is_snoozing:
      self.worker.on_volume.emit(True)

  def volume_down(self):
    if not self.card.is_snoozing:
      self.worker.on_volume.emit(False)


class ScreenHandler:
  def __init__(self, window, app):
    self.window = window
    self.screens = app.screens()

  def get_screen_geometry(self, screen_index=0):
    index = self.verify_screen_index(screen_index)
    screen = self.screens[index]
    screen_geometry = screen.geometry()

    return screen_geometry

  def verify_screen_index(self, screen_index=0):
    if screen_index > (len(self.screens) - 1):
      return len(self.screens) - 1
    elif screen_index < 0:
      return 0

    return screen_index
