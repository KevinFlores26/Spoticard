from utils.utils import (
    load_json,
    get_image_color,
    get_current_playback,
    get_total_width,
    convert_img_to_qt,
    set_timer
)

def_prefs = load_json(r"config\preferences_default.json")
user_prefs = load_json(r"config\preferences_user.json")

# Lambda get preferences (user and default as fallback)
get_pr = lambda key: user_prefs.get(key, def_prefs.get(key))


class UpdateHandler:
    def __init__(self, parent):
        self.parent = parent
        self.sp = parent.get_sp()

        self.previous_track_id = None
        self.previous_is_playing = None

        self.is_spotify_turn_on = True
        self.warning_card_shown = False

        self.update_timer = set_timer(self.update_card)

    def update_card(self):
        if self.update_timer.isActive():
            self.update_timer.stop()

        if self.parent.showing_card:
            self.update_timer.stop()
            return

        current_playback = get_current_playback(self.sp)

        if current_playback is None:
            self.is_spotify_turn_on = False

            if not self.is_spotify_turn_on and not self.warning_card_shown:
                title = "Not playing"
                artist = "Turn on Spotify or check your internet connection"
                pixmap = convert_img_to_qt(get_pr("song_image_size"), r"resources\img\warning.png", False)

                # Set properties
                self.card_filler(title, artist, pixmap)
                self.parent.animations.show_card()

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

                # Verify if the card is already showing (if so, hide it), then execute update_card_properties
                self.update_card_properties(current_track)

            # Update the previous state
            self.previous_track_id = current_track_id
            self.previous_is_playing = is_playing

        self.update_timer.start(1000)

    def update_card_properties(self, current_track):
        title = current_track["name"]
        artist = current_track["artists"][0]["name"]

        # Get and show the song's image
        img_url = current_track["album"]["images"][0]["url"]
        pixmap = convert_img_to_qt(get_pr("song_image_size"), img_url)
        image_color = get_image_color(img_url)

        # Set properties
        self.card_filler(title, artist, pixmap, image_color)
        self.parent.animations.show_card()

    def card_filler(
            self,
            title="No title",
            artist="No artist",
            pixmap=None,
            image_color=get_pr("custom_accent"),
    ):
        self.parent.title_label.setText(title)
        self.parent.artist_label.setText(artist)
        self.parent.bar.setStyleSheet(f"background-color: {image_color};")

        if pixmap:
            try:
                self.parent.img_label.setPixmap(pixmap)
            except Exception as e:
                print(f"Error: Image not found or not supported ({e})")
                self.parent.img_label.clear()
        else:
            self.parent.img_label.clear()

        # Set the card width manually
        total_width = get_total_width(
            self.parent.card_layout, get_pr("card_spacing"), get_pr("min_card_width")
        )
        self.parent.setFixedWidth(total_width)


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
