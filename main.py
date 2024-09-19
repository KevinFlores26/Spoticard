import spotipy
from spotipy.oauth2 import SpotifyOAuth
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import Qt, QPropertyAnimation, QTimeLine, QPoint, QEasingCurve
from PIL import Image
import requests
from io import BytesIO
from colorthief import ColorThief
from config import params as p
from config import urls

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=p['CLIENT_ID'],
    client_secret=p['CLIENT_SECRET'],
    redirect_uri=urls['REDIRECT_URI'],
    scope=p['SCOPE'])
)

previous_track_id = None
previous_is_playing = None


def get_image_color(image_url, accent = True):
    response = requests.get(image_url)
    img_data = BytesIO(response.content)
    color_thief = ColorThief(img_data)

    if accent:
        palette = color_thief.get_palette(color_count=3, quality=1)
        if len(palette) > 1:
            accent_color = palette[1]
            return '#%02x%02x%02x' % accent_color

    # If there isn't more than 1 color, it'll use predominant color instead
    dominant_color = color_thief.get_color(quality=1)
    return '#%02x%02x%02x' % dominant_color


class MusicCard(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.previous_track_id = None
        self.previous_is_playing = None

        # Main layout
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setStyleSheet("background-color: #202020;")

        self.setGeometry(-50, 30, 350, 120)
        self.card_layout = QtWidgets.QHBoxLayout(self)
        self.card_layout.setContentsMargins(0, 0, 20, 0)
        self.setLayout(self.card_layout)

        # Card's info
        self.bar = QtWidgets.QWidget(self)
        self.bar.setFixedSize(60, self.height())
        self.bar.setStyleSheet("background-color: #7538e4;")
        self.card_layout.addWidget(self.bar, 0)

        self.img_label = QtWidgets.QLabel(self)
        self.img_label.setFixedSize(64, 64)
        self.card_layout.addSpacing(10)
        self.card_layout.addWidget(self.img_label, 1)

        self.info_layout = QtWidgets.QVBoxLayout()
        self.info_layout.setAlignment(Qt.AlignVCenter)
        self.info_layout.setContentsMargins(10, 0, 10, 0)

        self.title_label = QtWidgets.QLabel("", self)
        self.title_label.setStyleSheet("color: white; font-size: 24px; font-family: 'Tsunagi Gothic Black', 'Filson Pro', Helvetica;")
        self.artist_label = QtWidgets.QLabel("", self)
        self.artist_label.setStyleSheet("color: white; font-size: 12px; font-family: 'Tsunagi Gothic Black', 'Filson Pro', Helvetica;")

        self.info_layout.addWidget(self.title_label)
        self.info_layout.addWidget(self.artist_label)
        self.card_layout.addLayout(self.info_layout)

        # Animations
        self.slide_in_animation = QPropertyAnimation(self, b"pos")
        self.slide_in_animation.setDuration(1500)
        self.slide_in_animation.setEasingCurve(QEasingCurve.OutBack)

        self.slide_out_animation = QPropertyAnimation(self, b"pos")
        self.slide_out_animation.setDuration(2000)
        self.slide_out_animation.setEasingCurve(QEasingCurve.InBack)

        self.timeline = QTimeLine(6000)  # How long will the card last in screen
        self.timeline.setFrameRange(0, 100)
        self.timeline.frameChanged.connect(self.start_fade_out)

        self.update_card()

    def update_card(self):
        current_playback = sp.current_playback()

        if current_playback:
            current_track = current_playback['item']
            is_playing = current_playback['is_playing']
            current_track_id = current_track['id']

            # Shows the card if the song changes, or it changes its state (pause to playing)
            if current_track_id != self.previous_track_id or (self.previous_is_playing == False and is_playing == True):
                self.title_label.setText(current_track['name'])
                self.artist_label.setText(', '.join([artist['name'] for artist in current_track['artists']]))

                # Get and show the song's image
                img_url = current_track['album']['images'][0]['url']
                response = requests.get(img_url)
                img_data = response.content
                img = Image.open(BytesIO(img_data))
                img = img.resize((64, 64), Image.Resampling.LANCZOS)
                img = img.convert("RGBA")

                data = img.tobytes("raw", "RGBA")
                qimage = QtGui.QImage(data, img.width, img.height, QtGui.QImage.Format_RGBA8888)
                pixmap = QtGui.QPixmap.fromImage(qimage)
                self.img_label.setPixmap(pixmap)

                # Apply dominant color to the vertical bar
                dominant_color = get_image_color(img_url)
                self.bar.setStyleSheet(f"background-color: {dominant_color};")

                self.show_card()
                self.timeline.start()

            # Update the previous state
            self.previous_track_id = current_track_id
            self.previous_is_playing = is_playing

        QtCore.QTimer.singleShot(1000, self.update_card)

    def show_card(self):
        # Slide in animation from left side of the screen
        start_pos = QPoint(-500, 30)
        end_pos = QPoint(-50, 30)
        self.slide_in_animation.setStartValue(start_pos)
        self.slide_in_animation.setEndValue(end_pos)
        self.slide_in_animation.start()

    def start_fade_out(self):
        if self.timeline.state() == QTimeLine.Running and self.timeline.currentFrame() == 100:
            self.hide_card()

    def hide_card(self):
        # Slide out animation
        start_pos = QPoint(-50, 30)
        end_pos = QPoint(-500, 30)
        self.slide_out_animation.setStartValue(start_pos)
        self.slide_out_animation.setEndValue(end_pos)
        self.slide_out_animation.start()

if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    card = MusicCard()
    card.show()
    app.exec_()
