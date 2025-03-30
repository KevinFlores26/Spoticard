import requests, time, re, threading
from PIL import Image
from PyQt5 import QtWidgets, QtGui, QtCore
from io import BytesIO
from colorthief import ColorThief
from utils.helpers import hex_to_rgb, color_distance, get_relative_path, apply_rounded_corners


# Core functions
def get_current_playback(sp, retries=3, delay=5):
  # Gets the current playback information and retry if it fails
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


# General functions
def set_timer(callback):
  # Sets a timer and return it
  timer = QtCore.QTimer()
  timer.timeout.connect(callback)

  return timer


def debounce(wait):
  # Debounces a function
  def decorator(fn):
    def debounced(*args, **kwargs):
      def call_it():
        fn(*args, **kwargs)

      if hasattr(debounced, '_timer'):
        debounced._timer.cancel()
      debounced._timer = threading.Timer(wait / 1000, call_it)
      debounced._timer.start()

    return debounced

  return decorator


def set_theme(card, card_labels, theme):
  # Sets the theme of the card
  card_style = change_stylesheet_property(card, "background-color", theme.get("bg_color"))
  card.setStyleSheet(card_style)

  title_style = change_stylesheet_property(card_labels[0], "color", theme.get("title_font_color"))
  card_labels[0].setStyleSheet(title_style)

  artist_style = change_stylesheet_property(card_labels[1], "color", theme.get("artist_font_color"))
  card_labels[1].setStyleSheet(artist_style)


def change_stylesheet_property(element, prop, value):
  # Changes or adds a specific stylesheet property of an element
  current_stylesheet = element.styleSheet()
  style = f"{prop}: {value};"

  if re.search(rf'\b{prop}\b:.*?;', current_stylesheet):
    return re.sub(rf'{prop}:.*?;', style, current_stylesheet)
  else:
    return current_stylesheet + style


# Image functions
def get_image_color(img_src, card_color, dominant=True, is_remote=True):
  # Get current song's image color
  img_data = None

  if isinstance(img_src, str):
    if is_remote and img_src.startswith("http"):
      response = requests.get(img_src)
      if response.status_code != 200:
        return None

      img_data = BytesIO(response.content)

    else:
      img_data = get_relative_path(img_src)

  elif isinstance(img_src, bytes):
    img_data = BytesIO(img_src)

  else:
    return None

  color_thief = ColorThief(img_data)

  palette = color_thief.get_palette(color_count=3, quality=1)
  dominant_color = color_thief.get_color(quality=1)
  accent_color = palette[1]

  if len(palette) > 1:
    rgb_card_color = hex_to_rgb(card_color)
    palette.pop(0) if dominant else None

    for color in palette:
      if color_distance(color, rgb_card_color) > 50:
        accent_color = color
        break
    return "#%02x%02x%02x" % (accent_color[0], accent_color[1], accent_color[2])

  # If there isn't more than 1 color, it'll use dominant color instead
  return "#%02x%02x%02x" % dominant_color


def convert_img_to_pixmap(img_size, img_src, is_remote=True, radius=5):
  try:
    if isinstance(img_src, str):
      if is_remote and img_src.startswith("http"):
        response = requests.get(img_src)
        if response.status_code != 200:
          return None

        img_data = response.content
        img = Image.open(BytesIO(img_data))

      else:
        img_path = get_relative_path(img_src)
        img = Image.open(img_path)

    elif isinstance(img_src, bytes):
      img = Image.open(BytesIO(img_src))

    else:
      return None

    img = img.resize((img_size, img_size), Image.Resampling.LANCZOS)
    img = img.convert("RGBA")

    data = img.tobytes("raw", "RGBA")
    qimage = QtGui.QImage(data, img.width, img.height, QtGui.QImage.Format_RGBA8888)
    pixmap = QtGui.QPixmap.fromImage(qimage)

    if radius > 0:
      pixmap = apply_rounded_corners(pixmap, radius)

    return pixmap

  except Exception as e:
    print(f"Error converting image: {e}")
    return None


def set_pixmap(container, pixmap):
  if not pixmap:
    container.img_label.clear()
    return

  try:
    container.img_label.setPixmap(pixmap)
  except Exception as e:
    print(f"Error: Image not found or not supported ({e})")
    container.img_label.clear()


# Layout functions
def assign_metadata(current_track, player):
  metadata = {
    "title": None,
    "artist": None,
    "album": None,
    "img_url": None,
    "img_bytes": None,  # image embedded from the track instead of a URL
    "filepath": None,
    "is_playing": None
  }

  if not current_track:
    return { }

  if player == "spotify":
    if current_track.get("currently_playing_type") == "ad":
      return { "case": "ad" }
    elif current_track.get("item") is None:
      return { "case": "no_track_info" }

    metadata["is_playing"] = current_track["is_playing"]
    current_track = current_track["item"]

    metadata["title"] = current_track["name"]
    metadata["artist"] = current_track["artists"][0]["name"]
    metadata["album"] = current_track["album"]["name"]
    metadata["img_url"] = current_track["album"]["images"][0]["url"]
  elif player == "foobar2000":
    metadata["title"] = current_track.get("title")
    metadata["artist"] = current_track.get("artist")
    metadata["album"] = current_track.get("album")
    metadata["img_url"] = current_track.get("img_url")
    metadata["img_bytes"] = current_track.get("img_bytes")
    metadata["filepath"] = current_track.get("filepath")
    metadata["is_playing"] = current_track.get("is_playing")

  return metadata


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

      if (
        isinstance(item.layout(), QtWidgets.QVBoxLayout)
        or isinstance(item.layout(), QtWidgets.QHBoxLayout)
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
  # Get the width of a container/layout with text
  relevant_width = 0

  for i in range(layout.count()):
    item = layout.itemAt(i)

    if isinstance(item.widget(), QtWidgets.QLabel):
      label = item.widget()
      text_width = label.fontMetrics().boundingRect(label.text()).width()

      if text_width > relevant_width:
        relevant_width = text_width

  return relevant_width
