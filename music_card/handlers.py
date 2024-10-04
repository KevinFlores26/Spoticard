from PyQt5 import QtGui, QtWidgets, QtCore
from PyQt5.QtCore import QTimer

from utils.utils import load_json, get_image_color, get_current_playback, get_total_width, convert_img_to_pixmap, set_timer, get_current_theme, set_theme
from utils.misc import THEME_NAMES
from utils.player_worker import PlayerWorker

def_prefs = load_json(r"config\preferences_default.json")
user_prefs = load_json(r"config\preferences_user.json")
themes = load_json(r"config\themes.json")

# Lambda get preferences (user and default as fallback)
get_pr = lambda key: user_prefs.get(key, def_prefs.get(key))


class UpdateHandler:
  def __init__(self, parent):
    self.parent = parent
    self.sp = parent.get_sp()

    self.previous_track_id = None
    self.previous_is_playing = None
    self.alert_card_shown = False
    self.update_timer = set_timer(self.update_card)

  # Main logic to show the card
  def update_card(self):
    if self.update_timer.isActive(): self.update_timer.stop()
    if self.parent.showing_card or self.parent.is_snoozing: return

    theme = get_current_theme(def_prefs, user_prefs, themes, self.parent.theme_name)
    current_playback = get_current_playback(self.sp)

    # Set theme if it was changed and show the card
    if self.parent.current_theme.get("THEME_NAME") != theme.get("THEME_NAME"):
      card_labels = [self.parent.title_label, self.parent.artist_label]
      set_theme(self.parent, card_labels, theme)
      self.parent.current_theme = theme

      current_track = current_playback["item"]
      self.update_card_properties(current_track)

    # Show warning card if Spotify is not connected
    elif current_playback is None and not self.alert_card_shown:
      title = "Not playing"
      artist = "Turn on Spotify or check your internet connection"
      pixmap = convert_img_to_pixmap(get_pr("image_size"), r"resources\img\warning.png", False)

      # Set properties
      self.update_card_properties(None, title, artist, pixmap)
      self.alert_card_shown = True
      self.previous_track_id = None

    # Show the card when the current track has not valid information
    elif current_playback and current_playback["item"] is None and not self.alert_card_shown:
      pixmap = convert_img_to_pixmap(get_pr("image_size"), r"resources\img\warning.png", False)
      self.update_card_properties(current_track=None, pixmap=pixmap)
      self.alert_card_shown = True
      self.previous_track_id = None

    # Show the card with the current track (normal case)
    elif current_playback and current_playback["item"]:
      self.alert_card_shown = False

      current_track = current_playback["item"]
      is_playing = current_playback["is_playing"]
      current_track_id = current_track["id"]

      # Shows the card if the song changes, or it changes its state (pause to playing)
      if (
        current_track_id != self.previous_track_id
        or self.previous_is_playing == False and is_playing == True
      ):
        self.previous_track_id = current_track_id
        self.previous_is_playing = is_playing

        # Verify if the card is already showing (if so, hide it), then execute update_card_properties
        self.update_card_properties(current_track)

      # Update the previous state
      self.previous_track_id = current_track_id
      self.previous_is_playing = is_playing

    self.update_timer.start(1000)

  def update_card_properties(
    self,
    current_track,
    title="No Title",
    artist="No Artist",
    pixmap=None,
    image_color=get_pr("custom_color"),
  ):
    self.reset_card_properties()

    if current_track:
      title = current_track["name"]
      artist = current_track["artists"][0]["name"]

      # Get and show the song's image
      img_url = current_track["album"]["images"][0]["url"]
      pixmap = convert_img_to_pixmap(get_pr("image_size"), img_url, True, get_pr("image_radius"))

      if not get_pr("only_custom_color"):
        image_color = get_image_color(img_url, self.parent.current_theme.get("bg_color"), get_pr("dominant_color"))

    # Set properties
    self.parent.title_label.setText(title)
    self.parent.artist_label.setText(artist)
    self.set_pixmap(pixmap)
    self.parent.bar.setStyleSheet(f"background-color: {image_color};")

    # Set the card width manually
    total_width = get_total_width(self.parent.card_layout, get_pr("card_spacing"), get_pr("min_card_width"))
    self.parent.setFixedWidth(total_width)

    # Update valid card's coordinates
    rect = self.parent.geometry()
    coords = {
      "upper_left": [get_pr("end_x_pos"), get_pr("end_y_pos")],
      "upper_right": [get_pr("end_x_pos") + rect.width(), get_pr("end_y_pos")],
      "lower_left": [get_pr("end_x_pos"), get_pr("end_y_pos") + rect.height()],
      "lower_right": [get_pr("end_x_pos") + rect.width(), get_pr("end_y_pos") + rect.height()],
    }
    self.parent.coords = coords
    self.parent.animations.show_card()

  def set_pixmap(self, pixmap):
    if not pixmap:
      self.parent.img_label.clear()
      return

    try:
      self.parent.img_label.setPixmap(pixmap)
    except Exception as e:
      print(f"Error: Image not found or not supported ({e})")
      self.parent.img_label.clear()

  def reset_card_properties(self):
    if self.parent.opacity_effect.opacity() == 0:
      self.parent.animations.fade_in()

    self.parent.bar.setStyleSheet(f"background-color: {get_pr('custom_accent')};")
    self.parent.title_label.setText("")
    self.parent.artist_label.setText("")
    self.parent.img_label.clear()


class CursorAndKeyHandler:
  def __init__(self, parent):
    self.parent = parent
    self.hover_timer = set_timer(self.parent.call_leave_event)

  def on_enter_or_click(self):
    if self.parent.is_faded_out:
      return

    self.parent.is_faded_out = True
    self.parent.animations.fade_out()

  def on_leave(self, force_show=False):
    if not self.parent.is_faded_out:
      self.hover_timer.stop()
      return

    if force_show:
      self.parent.is_faded_out = False
      self.parent.animations.fade_in()
      return

    c_pos = QtGui.QCursor.pos()  # cursor position
    u_left = self.parent.coords["upper_left"]
    l_right = self.parent.coords["lower_right"]

    # Check if the card left the screen
    if (
      c_pos.x() < u_left[0]
      or c_pos.y() < u_left[1]
      or c_pos.x() > l_right[0]
      or c_pos.y() > l_right[1]
    ):
      self.parent.is_faded_out = False
      self.parent.animations.fade_in()
    else:
      self.hover_timer.start(100)


class ShortcutHandler:
  def __init__(self, parent):
    self.parent = parent
    self.card = self.parent.card
    self.sp = self.card.get_sp()
    self.closing_timer = set_timer(self.exit_app)

    self.thread = QtCore.QThread()
    self.worker = PlayerWorker(self.sp)
    self.worker.moveToThread(self.thread)
    self.thread.start()

  # App related shortcuts
  def toggle_snooze(self):
    if self.card.is_snoozing:
      print("Awake...")
      self.card.is_snoozing = False
      self.card.updater.update_card()
    else:
      print("Snoozing...")
      if self.card.showing_card: self.card.animations.fade_out()
      self.card.is_snoozing = True

  def exit_app(self):
    print("Exiting...")
    if self.card.showing_card: self.card.animations.fade_out()
    QTimer.singleShot(500, lambda: QtWidgets.QApplication.quit())

  # Visual related shortcuts
  def toggle_card_visibility(self):
    if self.card.is_snoozing: return

    if not self.card.showing_card:
      self.card.animations.show_card()
    elif not self.card.is_faded_out and self.card.showing_card:
      self.card.cursor_handler.on_enter_or_click()
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
      self.worker.on_volume_up.emit()

  def volume_down(self):
    if not self.card.is_snoozing:
      self.worker.on_volume_down.emit()


class ScreenHandler:
  def __init__(self, parent, app):
    self.parent = parent
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
