import spotipy, requests
from spotipy.oauth2 import SpotifyOAuth
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import Qt, QTimeLine, QPropertyAnimation
from PIL import Image
from io import BytesIO

from utils.utils import (
    load_json,
    get_current_theme,
    get_image_color,
    get_current_playback,
    get_total_width,
)
from music_card.animations import MusicCardAnimations
from music_card.update_handler import UpdateHandler
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


class MusicCard(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.previous_track_id = None
        self.previous_is_playing = None

        self.is_spotify_turn_on = True
        self.warning_card_shown = False
        self.showing_card = False

        # Main layout
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setStyleSheet(f"background-color: {theme.get('bg_color', '#202020')};")
        self.move(get_pr("start_x_pos"), get_pr("start_y_pos"))
        self.setMinimumSize(get_pr("min_card_width"), get_pr("min_card_height"))
        self.setMaximumSize(get_pr("min_card_width") * 4, get_pr("min_card_height"))
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred
        )

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
        self.bar.setStyleSheet(
            f"background: {get_pr('custom_accent')};"
        )  # Accent color fallback
        self.card_layout.addWidget(self.bar, get_pr("color_bar_order"))
        self.card_layout.addSpacing(get_pr("card_spacing"))

        # Card's image
        self.img_label = QtWidgets.QLabel(self)
        self.img_label.setFixedSize(
            get_pr("song_image_size"), get_pr("song_image_size")
        )
        self.card_layout.addWidget(self.img_label, get_pr("card_order"))
        self.card_layout.addSpacing(get_pr("card_spacing"))

        # Card's info
        self.info_layout = QtWidgets.QVBoxLayout()
        self.info_layout.setAlignment(Qt.AlignVCenter)

        self.title_label = QtWidgets.QLabel("", self)
        self.title_label.setStyleSheet(
            f"color: {theme.get('title_font_color')}; font-size: {get_pr('title_font_size')}px; font-family: {get_pr('title_font')}"
        )
        self.artist_label = QtWidgets.QLabel("", self)
        self.artist_label.setStyleSheet(
            f"color: {theme.get('artist_font_color')}; font-size: {get_pr('artist_font_size')}px; font-family: {get_pr('artist_font')}"
        )

        self.info_layout.addWidget(self.title_label)
        self.info_layout.addWidget(self.artist_label)
        self.card_layout.addLayout(self.info_layout, get_pr("info_order"))

        # Animations
        self.slide_in_animation = QPropertyAnimation(self, b"pos")
        self.slide_out_animation = QPropertyAnimation(self, b"pos")
        self.fade_out_animation = QPropertyAnimation(self, b"windowOpacity")

        self.animations = MusicCardAnimations(self)

        # How long will the card last in screen
        self.timeline = QTimeLine(get_pr("total_card_dur"))
        self.timeline.setFrameRange(0, 100)
        self.timeline.frameChanged.connect(self.animations.start_hide_card)

        self.updater = UpdateHandler(self)
        self.updater.update_card(sp)

    def update_call(self, current_track):
        QtCore.QTimer.singleShot(0, lambda: self.updater.update_card_properties(current_track))

    def create_timeline(self):
        self.timeline = QTimeLine(get_pr("total_card_dur"))
        self.timeline.setFrameRange(0, 100)
        self.timeline.frameChanged.connect(self.animations.start_hide_card)


if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    card = MusicCard()
    card.show()
    app.exec_()
