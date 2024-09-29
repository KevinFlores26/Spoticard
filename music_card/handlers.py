from PyQt5 import QtGui
from utils.utils import (
  load_json,
  get_image_color,
  get_current_playback,
  get_total_width,
  convert_img_to_pixmap,
  set_timer,
  get_current_theme,
)

def_prefs = load_json(r"config\preferences_default.json")
user_prefs = load_json(r"config\preferences_user.json")
themes = load_json(r"config\themes.json")
theme = get_current_theme(def_prefs, user_prefs, themes)

# Lambda get preferences (user and default as fallback)
get_pr = lambda key: user_prefs.get(key, def_prefs.get(key))


class UpdateHandler:
  def __init__(self, parent):
    self.parent = parent
    self.sp = parent.get_sp()

    self.previous_track_id = None
    self.previous_is_playing = None
    self.warning_card_shown = False
    self.update_timer = set_timer(self.update_card)

  def update_card(self):
    if self.update_timer.isActive():
      self.update_timer.stop()
    if self.parent.showing_card:
      self.update_timer.stop()
      return

    current_playback = get_current_playback(self.sp)
    if current_playback is None and not self.warning_card_shown:
      title = "Not playing"
      artist = "Turn on Spotify or check your internet connection"
      pixmap = convert_img_to_pixmap(
        get_pr("song_image_size"), r"resources\img\warning.png", False
      )

      # Set properties
      self.update_card_properties(None, title, artist, pixmap)
      self.warning_card_shown = True
      self.previous_track_id = None

    elif current_playback:
      self.warning_card_shown = False

      current_track = current_playback["item"]
      is_playing = current_playback["is_playing"]
      current_track_id = current_track["id"]

      # Shows the card if the song changes, or it changes its state (pause to playing)
      if current_track_id != self.previous_track_id or (
        self.previous_is_playing == False and is_playing == True
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
    if current_track:
      title = current_track["name"]
      artist = current_track["artists"][0]["name"]

      # Get and show the song's image
      img_url = current_track["album"]["images"][0]["url"]
      pixmap = convert_img_to_pixmap(get_pr("song_image_size"), img_url)

      if not get_pr("only_custom_color"):
        image_color = get_image_color(
          img_url, theme.get("bg_color"), get_pr("dominant_color")
        )

    # Set properties
    self.parent.title_label.setText(title)
    self.parent.artist_label.setText(artist)
    self.set_pixmap(pixmap)
    self.parent.bar.setStyleSheet(f"background-color: {image_color};")

    # Set the card width manually
    total_width = get_total_width(
      self.parent.card_layout, get_pr("card_spacing"), get_pr("min_card_width")
    )
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


class CursorHandler:
  def __init__(self, parent):
    self.parent = parent
    self.hover_timer = set_timer(self.parent.call_leave_event)

  def on_enter(self):
    if self.parent.is_faded_out:
      return

    self.parent.is_faded_out = True
    self.parent.animations.fade_out()

  def on_leave(self):
    if not self.parent.is_faded_out:
      self.hover_timer.stop()
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
