from config.config import sp
from PyQt5.QtWidgets import QGraphicsOpacityEffect
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import Qt, QTimeLine, QPropertyAnimation, pyqtSignal
from utils.functions import get_pr, theme, set_timer
from ui.music_card.animations import MusicCardAnimations
from ui.music_card.handlers import UpdateHandler, ScreenHandler, CursorHandler, ShortcutHandler

class MusicCardWindow(QtWidgets.QMainWindow):
  if get_pr("shortcuts"):
    # Receive signals from shortcuts
    visibility_listener = pyqtSignal()
    theme_listener = pyqtSignal()
    play_pause_listener = pyqtSignal()
    shuffle_listener = pyqtSignal()
    repeat_listener = pyqtSignal()
    next_listener = pyqtSignal()
    previous_listener = pyqtSignal()
    volume_up_listener = pyqtSignal()
    volume_down_listener = pyqtSignal()
    snooze_listener = pyqtSignal()
    exit_listener = pyqtSignal()

  def __init__(self, app):
    super().__init__()
    if get_pr("only_on_desktop"):
      self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool)
    else:
      self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
    self.setAttribute(Qt.WA_TranslucentBackground)

    self.screen = ScreenHandler(self, app)
    self.screen_geo = self.screen.get_screen_geometry(get_pr("screen_index"))
    self.setFixedSize(self.screen_geo.width(), self.screen_geo.height())
    self.move(self.screen_geo.x(), self.screen_geo.y())

    self.card = MusicCard(self)
    self.card.setParent(self)
    if get_pr("always_on_screen"):
      self.card.move(abs(get_pr("fixed_x_pos")), abs(get_pr("fixed_y_pos")))
    else:
      self.card.move(get_pr("start_x_pos"), get_pr("start_y_pos"))

    # Shortcut handlers
    self.shortcut = ShortcutHandler(self)
    self.visibility_listener.connect(self.shortcut.toggle_card_visibility)
    self.theme_listener.connect(self.shortcut.toggle_theme)
    self.play_pause_listener.connect(self.shortcut.toggle_playback)
    self.next_listener.connect(self.shortcut.next_track)
    self.previous_listener.connect(self.shortcut.previous_track)
    self.shuffle_listener.connect(self.shortcut.toggle_shuffle)
    self.repeat_listener.connect(self.shortcut.toggle_repeat)
    self.volume_up_listener.connect(self.shortcut.volume_up)
    self.volume_down_listener.connect(self.shortcut.volume_down)
    self.snooze_listener.connect(self.shortcut.toggle_snooze)
    self.exit_listener.connect(self.shortcut.exit_app)


class MusicCard(QtWidgets.QFrame):
  def __init__(self, window):
    super().__init__(window)
    self.sp = sp
    self.theme_name = get_pr("theme")
    self.current_theme = theme
    self.tooltip_timer = set_timer(self.show_tooltip)

    self.showing_card = False
    if get_pr("always_on_screen"): self.showing_card = True
    self.is_faded_out = False
    self.is_snoozing = False

    self.tooltip_visible = False
    self.cursor_coords = None
    self.coords = None
    self.is_dragging = False
    self.drag_start_pos = QtCore.QPoint(abs(get_pr("fixed_x_pos")), abs(get_pr("fixed_y_pos")))
    self.setMouseTracking(True)

    # Main layout
    self.setStyleSheet(f"background-color: {theme.get('bg_color', '#202020')}; border-radius: {get_pr('card_radius')}px;")
    self.setFixedSize(get_pr("min_card_width"), get_pr("min_card_height"))

    self.card_layout = QtWidgets.QHBoxLayout(self)
    self.card_layout.setContentsMargins(
      get_pr("card_l_margin"),
      get_pr("card_t_margin"),
      get_pr("card_r_margin"),
      get_pr("card_b_margin"),
    )
    self.setLayout(self.card_layout)

    # Tooltip
    self.custom_tooltip = QtWidgets.QLabel("Testing", self)
    self.custom_tooltip.setStyleSheet(f"color: white; font-size: 10px; font-family: Poppins, Arial;")
    self.custom_tooltip.adjustSize()
    self.custom_tooltip.hide()

    # Color bar
    self.bar = QtWidgets.QWidget(self)
    self.bar.setFixedSize(60, self.height())
    self.bar.setStyleSheet(f"background: {get_pr('custom_accent')};")
    self.card_layout.addWidget(self.bar, get_pr("color_bar_order"))
    self.card_layout.addSpacing(get_pr("card_spacing"))

    # Card's image
    self.img_label = QtWidgets.QLabel(self)
    self.img_label.setFixedSize(get_pr("image_size"), get_pr("image_size"))
    self.card_layout.addWidget(self.img_label, get_pr("image_order"))
    self.card_layout.addSpacing(get_pr("card_spacing"))

    # Card's info
    self.info_layout = QtWidgets.QVBoxLayout()
    self.info_layout.setAlignment(Qt.AlignVCenter)

    label_style = (lambda label: f"color: {theme.get(f'{label}_font_color')}; font-size: {get_pr(f'{label}_font_size')}px; font-family: {get_pr(f'{label}_font')};")
    self.title_label = QtWidgets.QLabel("", self)
    self.title_label.setStyleSheet(label_style("title"))
    self.artist_label = QtWidgets.QLabel("", self)
    self.artist_label.setStyleSheet(label_style("artist"))

    self.info_layout.addWidget(self.title_label)
    self.info_layout.addWidget(self.artist_label)
    self.card_layout.addLayout(self.info_layout, get_pr("info_order"))

    # Animations
    self.slide_in_animation = QPropertyAnimation(self, b"pos")
    self.slide_out_animation = QPropertyAnimation(self, b"pos")

    self.opacity_effect = QGraphicsOpacityEffect(self)
    self.opacity_effect.setOpacity(0)
    self.setGraphicsEffect(self.opacity_effect)
    self.setAutoFillBackground(True)

    self.fade_in_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
    self.fade_out_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
    self.animations = MusicCardAnimations(self)

    # How long will the card last in screen
    self.timeline = QTimeLine(get_pr("total_card_dur"))
    self.timeline.setFrameRange(0, 100)
    self.timeline.frameChanged.connect(self.animations.start_hide_card)

    # Handlers
    self.updater = UpdateHandler(self)
    self.cursor_handler = CursorHandler(self)

    # Init
    self.updater.start_loop()

  # Card events
  def show_tooltip(self):
    self.tooltip_timer.stop()
    global_pos = QtGui.QCursor.pos()
    widget_pos = self.mapFromGlobal(global_pos)
    print(widget_pos)
    self.cursor_coords = widget_pos

    # if self.tooltip_visible or self.is_dragging:
    #  return
    # elif not self.tooltip_visible and :

    self.custom_tooltip.show()
    self.tooltip_visible = True

  def enterEvent(self, event):
    self.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
    self.tooltip_timer.start(2000)

    if not get_pr("hide_on_click"):
      self.cursor_handler.on_click()
      super().enterEvent(event)

  def leaveEvent(self, event):
    self.tooltip_timer.stop()
    self.cursor_handler.on_leave()
    super().leaveEvent(event)

  def call_leave_event(self):
    # Manual call to leave event
    q_event = QtCore.QEvent(QtCore.QEvent.Leave)
    self.leaveEvent(q_event)

  def mousePressEvent(self, event):
    if get_pr("always_on_screen") and get_pr("draggable") and event.button() == Qt.RightButton:
      self.setCursor(QtGui.QCursor(QtCore.Qt.OpenHandCursor))
      self.is_dragging = True
      self.drag_start_pos = event.globalPos() - self.frameGeometry().topLeft()
      event.accept()

    if get_pr("hide_on_click") and not self.is_faded_out and event.button() == Qt.LeftButton:
      self.cursor_handler.on_click()

  def mouseMoveEvent(self, event):
    if self.is_dragging:
      self.setCursor(QtGui.QCursor(QtCore.Qt.ClosedHandCursor))
      new_pos = event.globalPos() - self.drag_start_pos
      self.move(new_pos)
      event.accept()

  def mouseReleaseEvent(self, event):
    if get_pr("always_on_screen") and get_pr("draggable") and event.button() == Qt.RightButton:
      rect = self.geometry()
      pos = self.pos()
      coords = {
        "upper_left": (pos.x(), pos.y()),
        "upper_right": (pos.x() + rect.width(), pos.y()),
        "lower_left": (pos.x(), pos.y() + rect.height()),
        "lower_right": (pos.x() + rect.width(), pos.y() + rect.height()),
      }
      self.coords = coords

      self.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
      self.is_dragging = False
      event.accept()
