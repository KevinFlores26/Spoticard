import os, json, requests, darkdetect, time, re
from PIL import Image
from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtGui import QColor
from io import BytesIO
from colorthief import ColorThief
from utils.misc import hex_to_rgb, color_distance, get_relative_path, apply_rounded_corners


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
def load_json(file_path):
  # Loads a JSON file and returns its key: value as a dictionary
  relative_path = get_relative_path(file_path)

  if os.path.exists(relative_path) and os.path.getsize(relative_path) > 0:
    with open(relative_path, "r") as f:
      data = json.load(f)
      return data
  else:
    return { }


def set_timer(callback):
  # Sets a timer and return it
  timer = QtCore.QTimer()
  timer.timeout.connect(callback)

  return timer


def get_current_theme(def_prefs, user_prefs, themes, theme_name=""):
  # Returns the theme selected by the user
  theme = theme_name
  if theme_name == "":
    theme = user_prefs.get("theme", def_prefs.get("theme"))

  if theme == "user": return themes.get("user")
  if theme == "dark": return themes.get("dark")
  if theme == "light": return themes.get("light")

  # Adaptive theme as fallback
  if darkdetect.isDark():
    return themes.get("dark")
  else:
    return themes.get("light")


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
def get_image_color(image_url, card_color, dominant=True):
  # Get current song's image color
  response = requests.get(image_url)
  img_data = BytesIO(response.content)
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
    return "#%02x%02x%02x" % accent_color

  if dominant and len(palette) >= 1:
    return "#%02x%02x%02x" % dominant_color

  # If there isn't more than 1 color, it'll use dominant color instead
  return "#%02x%02x%02x" % dominant_color


def convert_img_to_pixmap(img_size, img_url, is_remote=True, radius=5):
  try:
    if is_remote:
      response = requests.get(img_url)
      img_data = response.content
      img = Image.open(BytesIO(img_data))
    else:
      img_path = get_relative_path(img_url)
      img = Image.open(img_path)

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


# Layout functions
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
