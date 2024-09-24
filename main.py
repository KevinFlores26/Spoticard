import spotipy, requests
from spotipy.oauth2 import SpotifyOAuth
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import Qt, QPropertyAnimation, QTimeLine, QPoint, QEasingCurve
from PIL import Image
from io import BytesIO

from utils.utils import (
    load_json,
    get_current_theme,
    get_image_color,
    EASING_FUNCTIONS,
    get_current_playback,
    get_total_width,
)
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

previous_track_id = None
previous_is_playing = None

def_prefs = load_json(r"config\preferences_default.json")
user_prefs = load_json(r"config\preferences_user.json")
themes = load_json(r"config\themes.json")
theme = get_current_theme(def_prefs, user_prefs, themes)

# Lambda get preferences (user and default as fallback)
get_pr = lambda key: user_prefs.get(key, def_prefs.get(key))


class MusicCard(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        print("Initializing...")

        self.previous_track_id = None
        self.previous_is_playing = None

        self.is_spotify_turn_on = True
        self.warning_card_shown = False

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

        # Card's info
        self.bar = QtWidgets.QWidget(self)
        self.bar.setFixedSize(60, self.height())
        self.bar.setStyleSheet(
            f"background: {get_pr('custom_accent')};"
        )  # Accent color fallback
        self.card_layout.addWidget(self.bar, get_pr("color_bar_order"))
        self.card_layout.addSpacing(get_pr("card_spacing"))

        self.img_label = QtWidgets.QLabel(self)
        self.img_label.setFixedSize(
            get_pr("song_image_size"), get_pr("song_image_size")
        )
        self.card_layout.addWidget(self.img_label, get_pr("card_order"))
        self.card_layout.addSpacing(get_pr("card_spacing"))

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
        self.slide_in_animation.setDuration(get_pr("open_animation_dur"))
        self.slide_in_animation.setEasingCurve(
            EASING_FUNCTIONS.get(get_pr("open_animation_easing"), QEasingCurve.Linear)
        )

        self.slide_out_animation = QPropertyAnimation(self, b"pos")
        self.slide_out_animation.setDuration(get_pr("close_animation_dur"))
        self.slide_out_animation.setEasingCurve(
            EASING_FUNCTIONS.get(get_pr("close_animation_easing"), QEasingCurve.Linear)
        )

        # How long will the card last in screen
        self.timeline = QTimeLine(get_pr("total_card_dur"))
        self.timeline.setFrameRange(0, 100)
        self.timeline.frameChanged.connect(self.start_hide_card)

        self.update_card()

    def update_card(self):
        current_playback = get_current_playback(sp)

        if current_playback is None:
            self.is_spotify_turn_on = False

            if not self.is_spotify_turn_on and not self.warning_card_shown:
                self.setWindowOpacity(1)

                self.bar.setStyleSheet(f"background: {get_pr('custom_accent')};")
                self.title_label.setText("Not playing")
                self.artist_label.setText(
                    "Turn on Spotify or check your internet connection"
                )
                self.img_label.clear()

                self.show_card()

                self.warning_card_shown = True
                self.previous_track_id = None

        elif current_playback:
            self.is_spotify_turn_on = True
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

                self.setWindowOpacity(1)

                self.title_label.setText(current_track["name"])
                self.artist_label.setText(
                    ", ".join([artist["name"] for artist in current_track["artists"]])
                )

                # Get and show the song's image
                img_url = current_track["album"]["images"][0]["url"]
                response = requests.get(img_url)
                img_data = response.content
                img = Image.open(BytesIO(img_data))
                img = img.resize(
                    (get_pr("song_image_size"), get_pr("song_image_size")),
                    Image.Resampling.LANCZOS,
                )
                img = img.convert("RGBA")

                data = img.tobytes("raw", "RGBA")
                qimage = QtGui.QImage(
                    data, img.width, img.height, QtGui.QImage.Format_RGBA8888
                )
                pixmap = QtGui.QPixmap.fromImage(qimage)
                self.img_label.setPixmap(pixmap)

                # Apply dominant color to the vertical bar
                image_color = get_image_color(img_url)
                self.bar.setStyleSheet(f"background-color: {image_color};")

                # Set the card width manually
                total_width = get_total_width(
                    self.card_layout, get_pr("card_spacing"), get_pr("min_card_width")
                )
                self.setFixedWidth(total_width)
                self.show_card()

            # Update the previous state
            self.previous_track_id = current_track_id
            self.previous_is_playing = is_playing

        QtCore.QTimer.singleShot(1000, self.update_card)

    def show_card(self):
        self.timeline.start()

        start_pos = QPoint(get_pr("start_x_pos"), get_pr("start_y_pos"))
        end_pos = QPoint(get_pr("end_x_pos"), get_pr("end_y_pos"))

        self.slide_in_animation.setStartValue(start_pos)
        self.slide_in_animation.setEndValue(end_pos)
        self.slide_in_animation.start()

    def start_hide_card(self):
        if (
                self.timeline.state() == QTimeLine.Running
                and self.timeline.currentFrame() == 100
        ):
            self.hide_card()

    def hide_card(self):
        rect = self.geometry()
        start_pos = QPoint(get_pr("end_x_pos"), get_pr("end_y_pos"))
        end_pos = QPoint(-rect.width(), get_pr("start_y_pos"))

        self.slide_out_animation.setStartValue(start_pos)
        self.slide_out_animation.setEndValue(end_pos)
        self.slide_out_animation.start()
        self.slide_out_animation.finished.connect(self.reset_card_properties)

    def reset_card_properties(self):
        # Reset card properties to avoid flickering or conflicts between animations
        self.bar.setStyleSheet("background-color: #000000;")
        self.title_label.setText("")
        self.artist_label.setText("")
        self.img_label.clear()
        self.setWindowOpacity(0)


if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    card = MusicCard()
    card.show()
    app.exec_()
