import requests
from PyQt5 import QtCore, QtGui, QtWidgets
from PIL import Image
from io import BytesIO

from utils.utils import (
    load_json,
    get_image_color,
    get_current_playback,
    get_total_width,
)

def_prefs = load_json(r"config\preferences_default.json")
user_prefs = load_json(r"config\preferences_user.json")

# Lambda get preferences (user and default as fallback)
get_pr = lambda key: user_prefs.get(key, def_prefs.get(key))

class UpdateHandler:
    def __init__(self, parent):
        self.parent = parent

        self.previous_track_id = None
        self.previous_is_playing = None

        self.is_spotify_turn_on = True
        self.warning_card_shown = False
        self.showing_card = False

    def update_card(self, sp):
        current_playback = get_current_playback(sp)

        if current_playback is None:
            self.is_spotify_turn_on = False

            if not self.is_spotify_turn_on and not self.warning_card_shown:
                self.parent.setWindowOpacity(1)

                self.parent.bar.setStyleSheet(f"background: {get_pr('custom_accent')};")
                self.parent.title_label.setText("Not playing")
                self.parent.artist_label.setText(
                    "Turn on Spotify or check your internet connection"
                )
                self.parent.img_label.clear()

                self.parent.show_card()

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

                self.parent.animations.on_change(current_track)

            # Update the previous state
            self.previous_track_id = current_track_id
            self.previous_is_playing = is_playing

        QtCore.QTimer.singleShot(1000, lambda: self.update_card(sp))

    def update_card_properties(self, current_track):
        self.parent.setWindowOpacity(1)

        self.parent.title_label.setText(current_track["name"])
        self.parent.artist_label.setText(
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
        self.parent.img_label.setPixmap(pixmap)

        # Apply dominant color to the vertical bar
        image_color = get_image_color(img_url)
        self.parent.bar.setStyleSheet(f"background-color: {image_color};")

        # Set the card width manually
        total_width = get_total_width(
            self.parent.card_layout, get_pr("card_spacing"), get_pr("min_card_width")
        )
        self.parent.setFixedWidth(total_width)

        QtWidgets.QApplication.processEvents()
        QtCore.QTimer.singleShot(0, self.parent.animations.show_card)
