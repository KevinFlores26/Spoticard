import os, json, requests, darkdetect
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


def load_json(file_path):
    # Loads a JSON file and returns its key: value as a dictionary

    project_root = os.path.dirname(os.path.dirname(__file__))
    relative_path = os.path.join(project_root, file_path)

    if os.path.exists(relative_path) and os.path.getsize(relative_path) > 0:
        with open(relative_path, "r") as f:
            print(f"Loading {relative_path}...")
            data = json.load(f)
            print(f"Content: {data}\n")
            return data
    else:
        print(f"File not found or is empty: {relative_path}\n")
        return {}
