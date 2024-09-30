import spotipy, keyboard
from PyQt5.QtWidgets import QGraphicsOpacityEffect
from spotipy.oauth2 import SpotifyOAuth
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import Qt, QTimeLine, QPropertyAnimation, pyqtSignal

from utils.utils import load_json, get_current_theme
from utils.misc import THEME_NAMES
from music_card.animations import MusicCardAnimations
from music_card.handlers import UpdateHandler, ScreenHandler, CursorAndKeyHandler
from config.config import params as p
from config.config import urls

sp = spotipy.Spotify(
  auth_manager=SpotifyOAuth(
    client_id=p["CLIENT_ID"],
    client_secret=p["CLIENT_SECRET"],
    redirect_uri=urls["REDIRECT_URI"],
    scope=p["SCOPE"],
  )
)

def_prefs = load_json(r"config\preferences_default.json")
user_prefs = load_json(r"config\preferences_user.json")
themes = load_json(r"config\themes.json")
theme = get_current_theme(def_prefs, user_prefs, themes)

# Lambda get preferences (user and default as fallback)
get_pr = lambda key: user_prefs.get(key, def_prefs.get(key))


class MusicCardWindow(QtWidgets.QMainWindow):
  visibility_listener = pyqtSignal()
  theme_listener = pyqtSignal()

  def __init__(self, app):
    super().__init__()
    self.visibility_listener.connect(self.toggle_card_visibility)
    self.theme_listener.connect(self.toggle_theme)

    self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
    self.setAttribute(Qt.WA_TranslucentBackground)

    self.screen = ScreenHandler(self, app)
    self.screen_geo = self.screen.get_screen_geometry(get_pr("screen_index"))
    self.setFixedSize(self.screen_geo.width(), self.screen_geo.height())
    self.move(self.screen_geo.x(), self.screen_geo.y())

    self.card = MusicCard(self)
    self.card.setParent(self)
    self.card.move(get_pr("start_x_pos"), get_pr("start_y_pos"))

  # Signal handlers
  def toggle_card_visibility(self):
    if not self.card.showing_card:
      self.card.animations.show_card()
    elif not self.card.is_faded_out and self.card.showing_card:
      self.card.cursor_handler.on_enter_or_click()
    elif self.card.is_faded_out:
      self.card.cursor_handler.on_leave(True)

  def toggle_theme(self):
    index = THEME_NAMES.index(self.card.theme_name)
    for name in THEME_NAMES:
      if name != THEME_NAMES[index]: continue

      next_theme_name = THEME_NAMES[(index + 1) % len(THEME_NAMES)]
      self.card.theme_name = next_theme_name
      return

    self.card.theme_name = THEME_NAMES[0]


class MusicCard(QtWidgets.QFrame):
  def __init__(self, parent):
    super().__init__(parent)
    self.theme_name = get_pr("theme")
    self.current_theme = theme
    self.showing_card = False
    self.is_faded_out = False
    self.coords = None
    self.setMouseTracking(True)

    # Main layout
    self.setStyleSheet(f"background-color: {theme.get('bg_color', '#202020')}; border-radius: {get_pr('card_radius')}px;")
    self.setFixedSize(get_pr("min_card_width"), get_pr("min_card_height"))

    self.card_layout = QtWidgets.QHBoxLayout(self)
    self.card_layout.setContentsMargins(
      get_pr("card_l_margin"),
      get_pr("card_t_margin"),
      get_pr("card_r_margin"),
      get_pr("card_b_margin"),
    )
    self.setLayout(self.card_layout)

    # Color bar
    self.bar = QtWidgets.QWidget(self)
    self.bar.setFixedSize(60, self.height())
    self.bar.setStyleSheet(f"background: {get_pr('custom_accent')};")
    self.card_layout.addWidget(self.bar, get_pr("color_bar_order"))
    self.card_layout.addSpacing(get_pr("card_spacing"))

    # Card's image
    self.img_label = QtWidgets.QLabel(self)
    self.img_label.setFixedSize(get_pr("image_size"), get_pr("image_size"))
    self.card_layout.addWidget(self.img_label, get_pr("card_order"))
    self.card_layout.addSpacing(get_pr("card_spacing"))

    # Card's info
    self.info_layout = QtWidgets.QVBoxLayout()
    self.info_layout.setAlignment(Qt.AlignVCenter)

    label_style = (lambda label: f"color: {theme.get(f'{label}_font_color')}; font-size: {get_pr(f'{label}_font_size')}px; font-family: {get_pr(f'{label}_font')};")
    self.title_label = QtWidgets.QLabel("", self)
    self.title_label.setStyleSheet(label_style("title"))
    self.artist_label = QtWidgets.QLabel("", self)
    self.artist_label.setStyleSheet(label_style("artist"))

    self.info_layout.addWidget(self.title_label)
    self.info_layout.addWidget(self.artist_label)
    self.card_layout.addLayout(self.info_layout, get_pr("info_order"))

    # Animations
    self.slide_in_animation = QPropertyAnimation(self, b"pos")
    self.slide_out_animation = QPropertyAnimation(self, b"pos")

    self.opacity_effect = QGraphicsOpacityEffect(self)
    self.opacity_effect.setOpacity(1.0)
    self.setGraphicsEffect(self.opacity_effect)
    self.setAutoFillBackground(True)

    self.fade_in_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
    self.fade_out_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
    self.animations = MusicCardAnimations(self)

    # How long will the card last in screen
    self.timeline = QTimeLine(get_pr("total_card_dur"))
    self.timeline.setFrameRange(0, 100)
    self.timeline.frameChanged.connect(self.animations.start_hide_card)

    # Handlers
    self.updater = UpdateHandler(self)
    self.cursor_handler = CursorAndKeyHandler(self)

    # Init
    self.updater.update_card()

  @staticmethod
  def get_sp():
    return sp

  # Card events
  def enterEvent(self, event):
    if not get_pr("hide_on_click"):
      self.cursor_handler.on_enter_or_click()
      super().enterEvent(event)

  def leaveEvent(self, event):
    self.cursor_handler.on_leave()
    super().leaveEvent(event)

  def call_leave_event(self):
    # Manual call to leave event
    q_event = QtCore.QEvent(QtCore.QEvent.Leave)
    self.leaveEvent(q_event)

  def mousePressEvent(self, event):
    if get_pr("hide_on_click") and not self.is_faded_out:
      self.cursor_handler.on_enter_or_click()


# Run the app
if __name__ == "__main__":
  app = QtWidgets.QApplication([])
  card_window = MusicCardWindow(app)


  # Add shortcut listener @formatter:off
  def on_shortcut_visibility(): card_window.visibility_listener.emit()
  def on_shortcut_theme(): card_window.theme_listener.emit()

  keyboard.add_hotkey(get_pr("visibility_shortcut"), on_shortcut_visibility)
  keyboard.add_hotkey(get_pr("theme_shortcut"), on_shortcut_theme)

  card_window.show()
  app.exec_()
