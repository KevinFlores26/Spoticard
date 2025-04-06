import re
from PyQt5.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QLabel, QLayout, QWidget, QGraphicsOpacityEffect
from PyQt5.QtCore import QPoint, Qt, QEvent
from PyQt5.QtGui import QCursor
from typing import TYPE_CHECKING

from config.config_main import config
from ui.music_card.components.tooltip import Tooltip
from ui.music_card.animations import MusicCardAnimations
from ui.music_card.handlers import UpdateHandler, CursorHandler

if TYPE_CHECKING: # Imports only for type annotations purposes (ignored at runtime)
  from PyQt5.QtWidgets import QLayoutItem
  from PyQt5.QtCore import QRect, QTimer
  from PyQt5.QtGui import QPixmap

  from media_players.base import PlaybackInfoDict
  from ui.music_card.window import MusicCardWindow

class MusicCard(QFrame):
  def __init__(self, window: "MusicCardWindow") -> None:
    super().__init__(window)
    self.coords: dict[str, tuple[int, int]] | None = None
    self.is_card_showing: bool = True if config.get_pr("always_on_screen") else False
    self.is_faded_out: bool = False
    self.is_snoozing: bool = False
    self.tooltip_visible: bool = False

    # Cursor-related Variables
    self.is_dragging: bool = False
    self.cursor_coords: QPoint | None = None
    self.drag_start_pos: QPoint = QPoint(abs(config.get_pr("fixed_x_pos")), abs(config.get_pr("fixed_y_pos")))
    self.setMouseTracking(True)

    # Main Layout
    self.setStyleSheet(f"background-color: {config.current_theme.get('bg_color', '#202020')}; border-radius: {config.get_pr('card_radius')}px;")
    self.setFixedSize(config.get_pr("min_card_width"), config.get_pr("min_card_height"))
    #self.setAutoFillBackground(True)

    self.main_layout: QHBoxLayout = QHBoxLayout(self)
    self.main_layout.setContentsMargins(*self.get_margins())
    self.setLayout(self.main_layout)

    # Color Bar
    self.bar: QWidget = QWidget(self)
    self.bar.setFixedSize(60, self.height())
    self.bar.setStyleSheet(f"background: {config.get_pr('custom_accent')};")
    self.main_layout.addWidget(self.bar, config.get_pr("color_bar_order"))
    self.main_layout.addSpacing(config.get_pr("card_spacing"))

    # Card's Image
    self.img_label: QLabel = QLabel(self)
    self.img_label.setFixedSize(config.get_pr("image_size"), config.get_pr("image_size"))
    self.main_layout.addWidget(self.img_label, config.get_pr("image_order"))
    self.main_layout.addSpacing(config.get_pr("card_spacing"))

    # Card's Info
    self.info_layout: QVBoxLayout = QVBoxLayout()
    self.info_layout.setAlignment(Qt.AlignVCenter)

    self.title_label: QLabel = QLabel("", self)
    self.title_label.setStyleSheet(self.get_label_style("title"))
    self.artist_label: QLabel = QLabel("", self)
    self.artist_label.setStyleSheet(self.get_label_style("artist"))

    self.info_layout.addWidget(self.title_label)
    self.info_layout.addWidget(self.artist_label)
    self.main_layout.addLayout(self.info_layout, config.get_pr("info_order"))

    # Components
    self.tooltip_class: Tooltip = Tooltip(self)
    self.tooltip_timer: "QTimer" = self.tooltip_class.tooltip_timer
    self.tooltip: QLabel = self.tooltip_class.get_tooltip()

    # Animations
    self.opacity_effect: QGraphicsOpacityEffect = QGraphicsOpacityEffect(self)
    self.opacity_effect.setOpacity(0)
    self.setGraphicsEffect(self.opacity_effect)

    self.animations: MusicCardAnimations = MusicCardAnimations(self)

    # Global Handlers
    self.playback_info: "PlaybackInfoDict" = {
      "current_track_id": '',
      "current_track": { },
      "is_playing": False,
      "previous_track_id": '',
      "previous_state_is_playing": False,
      "shuffle_state": False,
      "repeat_state": "off",
      "volume_percent": 0
    }

    self.updater: UpdateHandler = UpdateHandler(self)
    self.cursor_handler: CursorHandler = CursorHandler(self)

    # Initialize
    self.updater.start_loop()

  # Build Helpers
  @staticmethod
  def get_margins() -> tuple[int, int, int, int]:
    return config.get_pr("card_l_margin"), config.get_pr("card_t_margin"), config.get_pr("card_r_margin"), config.get_pr("card_b_margin")

  @staticmethod
  def get_label_style(label: str) -> str:
    color: str = f"color: {config.current_theme.get(f'{label}_font_color')}; "
    font_size: str = f"font-size: {config.get_pr(f'{label}_font_size')}px; "
    font_family: str = f"font-family: {config.get_pr(f'{label}_font')}; "

    return color + font_size + font_family

  # Getters
  def get_total_width(self, layout: QLayout, spacing: int = 10, min_width: int = 0) -> int:
    # Get the total width of an entire layout
    total_width: int = 0

    for i in range(layout.count()):
      item: "QLayoutItem" = layout.itemAt(i)

      if item.widget():
        widget_width: int = item.widget().sizeHint().width()

        if widget_width == -1:
          widget_width = item.widget().width()

        total_width += widget_width

      elif item.layout():
        layout_width: int = item.layout().sizeHint().width()

        if isinstance(item.layout(), QLayout):
          layout_width = self.get_width_container_text(item.layout())

        total_width += layout_width

    # Add spacing and margins to the total width
    total_width += (layout.count() - 1) * spacing
    left_margin, top_margin, right_margin, bottom_margin = layout.getContentsMargins()
    total_width += left_margin + right_margin

    if total_width < min_width:
      total_width = min_width

    print(f"Total width: {total_width}")
    return total_width

  @staticmethod
  def get_width_container_text(layout: QLayout) -> int:
    # Get the width of a container/layout with text
    relevant_width: int = 0

    for i in range(layout.count()):
      item: "QLayoutItem" = layout.itemAt(i)

      if isinstance(item.widget(), QLabel):
        label: QLabel = item.widget()
        text_width: int = label.fontMetrics().boundingRect(label.text()).width()

        if text_width > relevant_width:
          relevant_width = text_width

    return relevant_width

  # Properties Setters
  @staticmethod
  def modify_stylesheet(element: QWidget, prop: str, value: str) -> None:
    # Changes or adds a specific stylesheet property of an element
    current_stylesheet: str = element.styleSheet()
    style: str = f"{prop}: {value};"

    if re.search(rf'\b{prop}\b:.*?;', current_stylesheet):
      new_stylesheet: str = re.sub(rf'{prop}:.*?;', style, current_stylesheet)
      element.setStyleSheet(new_stylesheet)
    else:
      new_stylesheet: str = current_stylesheet + style
      element.setStyleSheet(new_stylesheet)

  @staticmethod
  def set_pixmap(container: QWidget, pixmap: "QPixmap") -> None:
    if not pixmap:
      container.img_label.clear()
      return

    try:
      container.img_label.setPixmap(pixmap)

    except Exception as e:
      print(f"Error: Image not found or not supported ({e})")
      container.img_label.clear()

  def set_theme(self, theme: dict[str, str] | None = None) -> None:
    if not theme:
      theme = config.current_theme

    self.modify_stylesheet(self, "background-color", theme.get("bg_color"))
    self.modify_stylesheet(self.title_label, "color", theme.get("title_font_color"))
    self.modify_stylesheet(self.artist_label, "color", theme.get("artist_font_color"))

  # Events
  def enterEvent(self, event) -> None:
    self.setCursor(QCursor(Qt.PointingHandCursor))
    self.tooltip_timer.start(2000)

    if not config.get_pr("hide_on_click"):
      self.cursor_handler.on_click()
      super().enterEvent(event)

  def leaveEvent(self, event) -> None:
    self.tooltip_timer.stop()
    self.cursor_handler.on_leave()
    super().leaveEvent(event)

  def call_leave_event(self) -> None: # Manual call to leave event
    q_event: QEvent = QEvent(QEvent.Leave)
    self.leaveEvent(q_event)

  def mousePressEvent(self, event) -> None:
    if config.get_pr("always_on_screen") and config.get_pr("draggable") and event.button() == Qt.RightButton:
      self.setCursor(QCursor(Qt.OpenHandCursor))
      self.is_dragging = True
      self.drag_start_pos = event.globalPos() - self.frameGeometry().topLeft()
      event.accept()

    if config.get_pr("hide_on_click") and not self.is_faded_out and event.button() == Qt.LeftButton:
      self.cursor_handler.on_click()

  def mouseMoveEvent(self, event) -> None:
    if self.is_dragging:
      self.setCursor(QCursor(Qt.ClosedHandCursor))
      new_pos: QPoint = event.globalPos() - self.drag_start_pos
      self.move(new_pos)
      event.accept()

  def mouseReleaseEvent(self, event) -> None:
    if config.get_pr("always_on_screen") and config.get_pr("draggable") and event.button() == Qt.RightButton:
      rect: "QRect" = self.geometry()
      pos: QPoint = self.pos()
      coords: dict[str, tuple[int, int]] = {
        "upper_left": (pos.x(), pos.y()),
        "upper_right": (pos.x() + rect.width(), pos.y()),
        "lower_left": (pos.x(), pos.y() + rect.height()),
        "lower_right": (pos.x() + rect.width(), pos.y() + rect.height()),
      }
      self.coords = coords

      self.setCursor(QCursor(Qt.PointingHandCursor))
      self.is_dragging = False
      event.accept()
