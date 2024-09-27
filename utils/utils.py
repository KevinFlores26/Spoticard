import os, json, requests, darkdetect, time
from PIL import Image
from PyQt5 import QtWidgets, QtGui
from PyQt5.QtCore import QEasingCurve as Ease
from io import BytesIO
from colorthief import ColorThief

EASING_FUNCTIONS = {
    "InSine": Ease.InSine,
    "OutSine": Ease.OutSine,
    "InOutSine": Ease.InOutSine,
    "InQuad": Ease.InQuad,
    "OutQuad": Ease.OutQuad,
    "InOutQuad": Ease.InOutQuad,
    "InCubic": Ease.InCubic,
    "OutCubic": Ease.OutCubic,
    "InOutCubic": Ease.InOutCubic,
    "InQuart": Ease.InQuart,
    "OutQuart": Ease.OutQuart,
    "InOutQuart": Ease.InOutQuart,
    "InQuint": Ease.InQuint,
    "OutQuint": Ease.OutQuint,
    "InOutQuint": Ease.InOutQuint,
    "InExpo": Ease.InExpo,
    "OutExpo": Ease.OutExpo,
    "InOutExpo": Ease.InOutExpo,
    "InCirc": Ease.InCirc,
    "OutCirc": Ease.OutCirc,
    "InOutCirc": Ease.InOutCirc,
    "InBack": Ease.InBack,
    "OutBack": Ease.OutBack,
    "InOutBack": Ease.InOutBack,
    "InElastic": Ease.InElastic,
    "OutElastic": Ease.OutElastic,
    "InOutElastic": Ease.InOutElastic,
    "InBounce": Ease.InBounce,
    "OutBounce": Ease.OutBounce,
    "InOutBounce": Ease.InOutBounce,
}


def get_current_theme(def_prefs, user_prefs, themes):
    # Returns the theme selected by the user
    theme = user_prefs.get("theme", def_prefs.get("theme"))

    if theme == "user":
        return themes.get("user")

    if theme == "dark":
        return themes.get("dark")
    if theme == "light":
        return themes.get("light")

    # Adaptive theme as fallback
    print(f"Adaptive theme detected -> {darkdetect.theme()}")
    if darkdetect.isDark():
        return themes.get("dark")
    else:
        return themes.get("light")


def get_image_color(image_url, accent=True):
    # Get current song's image color
    response = requests.get(image_url)
    img_data = BytesIO(response.content)
    color_thief = ColorThief(img_data)

    if accent:
        palette = color_thief.get_palette(color_count=3, quality=1)
        if len(palette) > 1:
            accent_color = palette[1]
            return "#%02x%02x%02x" % accent_color

    # If there isn't more than 1 color, it'll use predominant color instead
    dominant_color = color_thief.get_color(quality=1)
    return "#%02x%02x%02x" % dominant_color


def get_relative_path(file_path):
    project_root = os.path.dirname(os.path.dirname(__file__))
    relative_path = os.path.join(project_root, file_path)
    return relative_path


def load_json(file_path):
    # Loads a JSON file and returns its key: value as a dictionary
    relative_path = get_relative_path(file_path)

    if os.path.exists(relative_path) and os.path.getsize(relative_path) > 0:
        with open(relative_path, "r") as f:
            print(f"Loading {relative_path}...")
            data = json.load(f)
            print(f"Content: {data}\n")
            return data
    else:
        print(f"File not found or is empty: {relative_path}\n")
        return {}


def get_current_playback(sp, retries=3, delay=5):
    # Get current playback and retry if it fails
    for attempt in range(retries):
        try:
            current_playback = sp.current_playback()
            return current_playback

        except requests.exceptions.ReadTimeout:
            print(
                f"ReadTimeout error. Retry {attempt + 1} of {retries} in {delay} seconds..."
            )
            time.sleep(delay)
        except requests.exceptions.RequestException as e:
            print(f"Other request error: {e}")
            return None

    return None


def convert_img_to_qt(img_size, img_url, is_remote=True):
    try:
        if is_remote:
            response = requests.get(img_url)
            img_data = response.content
            img = Image.open(BytesIO(img_data))
        else:
            img_path = get_relative_path(img_url)
            img = Image.open(img_path)

        img = img.resize(
            (img_size, img_size),
            Image.Resampling.LANCZOS,
        )
        img = img.convert("RGBA")

        data = img.tobytes("raw", "RGBA")
        qimage = QtGui.QImage(data, img.width, img.height, QtGui.QImage.Format_RGBA8888)
        pixmap = QtGui.QPixmap.fromImage(qimage)
        return pixmap

    except Exception as e:
        print(f"Error converting image: {e}")
        return None


def get_total_width(layout, spacing=10, min_width=0):
    # Get the total width of the whole layout
    total_width = 0

    for i in range(layout.count()):
        item = layout.itemAt(i)

        if item.widget():
            widget_width = item.widget().sizeHint().width()

            if widget_width == -1:
                widget_width = item.widget().width()

            total_width += widget_width
        elif item.layout():
            layout_width = item.layout().sizeHint().width()

            if isinstance(item.layout(), QtWidgets.QVBoxLayout) or isinstance(
                    item.layout(), QtWidgets.QHBoxLayout
            ):
                layout_width = get_width_container_text(item.layout())

            total_width += layout_width

    # Add spacing and margins to the total width
    total_width += (layout.count() - 1) * spacing
    left_margin, top_margin, right_margin, bottom_margin = layout.getContentsMargins()
    total_width += left_margin + right_margin

    if total_width < min_width:
        total_width = min_width

    print(f"Total width: {total_width}")
    return total_width


def get_width_container_text(layout):
    # Get the width of a container with text
    relevant_width = 0

    for i in range(layout.count()):
        item = layout.itemAt(i)

        if isinstance(item.widget(), QtWidgets.QLabel):
            label = item.widget()
            text_width = label.fontMetrics().boundingRect(label.text()).width()

            if text_width > relevant_width:
                relevant_width = text_width

    return relevant_width
