from PyQt5.QtCore import QEasingCurve, QPoint, QTimeLine, QPropertyAnimation
from typing import TYPE_CHECKING
from config.config_main import config
from utils.constants import EASING_FUNCTIONS

if TYPE_CHECKING:  # Imports only for type annotations purposes (ignored at runtime)
  from PyQt5.QtCore import QRect
  from ui.music_card.card import MusicCard

class MusicCardAnimations:
  def __init__(self, card: "MusicCard") -> None:
    self.card: "MusicCard" = card
    self.last_x: int = config.get_pr("start_x_pos")

    # Animations' Properties
    self.slide_in_animation: QPropertyAnimation = QPropertyAnimation(self.card, b"pos")
    self.slide_in_animation.setDuration(config.get_pr("open_animation_dur"))
    self.slide_in_animation.setEasingCurve(self.get_easing_curve("open_animation_easing"))

    self.slide_out_animation: QPropertyAnimation = QPropertyAnimation(self.card, b"pos")
    self.slide_out_animation.setDuration(config.get_pr("close_animation_dur"))
    self.slide_out_animation.setEasingCurve(self.get_easing_curve("close_animation_easing"))
    self.slide_out_animation.finished.connect(self.restart_loop)

    self.fade_out_animation: QPropertyAnimation = QPropertyAnimation(self.card.opacity_effect, b"opacity")
    self.fade_out_animation.setDuration(300)
    self.fade_out_animation.setEasingCurve(QEasingCurve.OutCubic)

    self.fade_in_animation: QPropertyAnimation = QPropertyAnimation(self.card.opacity_effect, b"opacity")
    self.fade_in_animation.setDuration(300)
    self.fade_in_animation.setEasingCurve(QEasingCurve.InCubic)

    self.timeline: QTimeLine = QTimeLine(config.get_pr("total_card_dur"))
    self.timeline.setFrameRange(0, 100)
    self.timeline.frameChanged.connect(self.start_hide_card)

  @staticmethod
  def get_easing_curve(curve: str, from_pref: bool = True) -> QEasingCurve:
    if from_pref:
      return EASING_FUNCTIONS.get(config.get_pr(curve), QEasingCurve.Linear)

    return EASING_FUNCTIONS.get(curve, QEasingCurve.Linear)

  # Main Card Timeline (Animations), in order of appearance
  def show_card(self) -> None:
    if config.get_pr("always_on_screen"):
      return

    if self.slide_in_animation.state() == QPropertyAnimation.Running:
      self.slide_in_animation.stop()

    self.timeline.start()
    self.card.is_card_showing = True

    start_pos: QPoint = QPoint(self.last_x, config.get_pr("start_y_pos"))
    end_pos: QPoint = QPoint(config.get_pr("end_x_pos"), config.get_pr("end_y_pos"))

    self.slide_in_animation.setStartValue(start_pos)
    self.slide_in_animation.setEndValue(end_pos)
    self.slide_in_animation.start()

  def start_hide_card(self) -> None:
    if self.timeline.state() == QTimeLine.Running and self.timeline.currentFrame() == 100:
      self.hide_card()

  def hide_card(self) -> None:
    if config.get_pr("always_on_screen"):
      return

    rect: "QRect" = self.card.geometry()
    start_pos: QPoint = QPoint(config.get_pr("end_x_pos"), config.get_pr("end_y_pos"))
    end_pos: QPoint = QPoint(-rect.width(), config.get_pr("start_y_pos"))

    self.slide_out_animation.setStartValue(start_pos)
    self.slide_out_animation.setEndValue(end_pos)
    self.slide_out_animation.start()

  def restart_loop(self) -> None:
    # Reset some properties and restart the loop
    if self.timeline.state() == QTimeLine.Running: self.timeline.stop()
    if self.card.opacity_effect.opacity() == 0: self.fade_in()

    rect: "QRect" = self.card.geometry()
    self.last_x = rect.x()

    self.card.is_card_showing = False
    self.card.updater.loop_timer.start(1000)

  # Card Hover Animations
  def fade_out(self) -> None:
    if self.fade_in_animation.state() == QPropertyAnimation.Running: self.fade_in_animation.stop()
    if self.fade_out_animation.state() == QPropertyAnimation.Running: self.fade_out_animation.stop()

    self.fade_out_animation.setStartValue(1.0)
    self.fade_out_animation.setEndValue(0)
    self.fade_out_animation.start()

  def fade_in(self) -> None:
    if self.fade_in_animation.state() == QPropertyAnimation.Running: self.fade_in_animation.stop()
    if self.fade_out_animation.state() == QPropertyAnimation.Running: self.fade_out_animation.stop()

    self.fade_in_animation.setStartValue(0)
    self.fade_in_animation.setEndValue(1.0)
    self.fade_in_animation.start()
