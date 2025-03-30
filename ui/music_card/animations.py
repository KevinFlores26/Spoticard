from PyQt5.QtCore import QEasingCurve, QPoint, QTimeLine, QPropertyAnimation
from config.config_main import config
from utils.helpers import EASING_FUNCTIONS


class MusicCardAnimations:
  def __init__(self, card):
    self.card = card
    self.last_x = config.get_pr("start_x_pos")

    # Set animations properties
    self.slide_in_animation = self.card.slide_in_animation
    self.slide_in_animation.setDuration(config.get_pr("open_animation_dur"))
    self.slide_in_animation.setEasingCurve(EASING_FUNCTIONS.get(config.get_pr("open_animation_easing"), QEasingCurve.Linear))

    self.slide_out_animation = self.card.slide_out_animation
    self.slide_out_animation.setDuration(config.get_pr("close_animation_dur"))
    self.slide_out_animation.setEasingCurve(EASING_FUNCTIONS.get(config.get_pr("close_animation_easing"), QEasingCurve.Linear))
    self.slide_out_animation.finished.connect(self.restart_loop)

    self.fade_out_animation = self.card.fade_out_animation
    self.fade_out_animation.setDuration(300)
    self.fade_out_animation.setEasingCurve(QEasingCurve.OutCubic)

    self.fade_in_animation = self.card.fade_in_animation
    self.fade_in_animation.setDuration(300)
    self.fade_in_animation.setEasingCurve(QEasingCurve.InCubic)

  # Main card timeline (animations), in order of appearance
  def show_card(self):
    if config.get_pr("always_on_screen"): return
    if self.slide_in_animation.state() == QPropertyAnimation.Running:
      self.slide_in_animation.stop()

    self.card.timeline.start()
    self.card.showing_card = True

    start_pos = QPoint(self.last_x, config.get_pr("start_y_pos"))
    end_pos = QPoint(config.get_pr("end_x_pos"), config.get_pr("end_y_pos"))

    self.slide_in_animation.setStartValue(start_pos)
    self.slide_in_animation.setEndValue(end_pos)
    self.slide_in_animation.start()

  def start_hide_card(self):
    if (
      self.card.timeline.state() == QTimeLine.Running
      and self.card.timeline.currentFrame() == 100
    ):
      self.hide_card()

  def hide_card(self):
    if config.get_pr("always_on_screen"): return

    rect = self.card.geometry()
    start_pos = QPoint(config.get_pr("end_x_pos"), config.get_pr("end_y_pos"))
    end_pos = QPoint(-rect.width(), config.get_pr("start_y_pos"))

    self.slide_out_animation.setStartValue(start_pos)
    self.slide_out_animation.setEndValue(end_pos)
    self.slide_out_animation.start()

  def restart_loop(self):
    # Reset some properties and restart the loop
    if self.card.timeline.state() == QTimeLine.Running: self.card.timeline.stop()
    if self.card.opacity_effect.opacity() == 0: self.fade_in()

    rect = self.card.geometry()
    self.last_x = rect.x()

    self.card.showing_card = False
    self.card.updater.loop_timer.start(1000)

  # Card hover animations
  def fade_out(self):
    if self.fade_in_animation.state() == QPropertyAnimation.Running: self.fade_in_animation.stop()
    if self.fade_out_animation.state() == QPropertyAnimation.Running: self.fade_out_animation.stop()

    self.fade_out_animation.setStartValue(1.0)
    self.fade_out_animation.setEndValue(0)
    self.fade_out_animation.start()

  def fade_in(self):
    if self.fade_in_animation.state() == QPropertyAnimation.Running: self.fade_in_animation.stop()
    if self.fade_out_animation.state() == QPropertyAnimation.Running: self.fade_out_animation.stop()

    self.fade_in_animation.setStartValue(0)
    self.fade_in_animation.setEndValue(1.0)
    self.fade_in_animation.start()
