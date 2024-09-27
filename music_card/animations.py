from PyQt5.QtCore import QEasingCurve, QPoint, QTimeLine, QPropertyAnimation
from utils.utils import load_json, EASING_FUNCTIONS

def_prefs = load_json(r"config\preferences_default.json")
user_prefs = load_json(r"config\preferences_user.json")

# Lambda get preferences (user and default as fallback)
get_pr = lambda key: user_prefs.get(key, def_prefs.get(key))

class MusicCardAnimations:
    def __init__(self, parent):
        self.parent = parent
        self.sp = parent.get_sp()
        self.last_x = get_pr("start_x_pos")

        self.slide_in_animation = self.parent.slide_in_animation
        self.slide_in_animation.setDuration(get_pr("open_animation_dur"))
        self.slide_in_animation.setEasingCurve(
            EASING_FUNCTIONS.get(get_pr("open_animation_easing"), QEasingCurve.Linear)
        )

        self.slide_out_animation = self.parent.slide_out_animation
        self.slide_out_animation.setDuration(get_pr("close_animation_dur"))
        self.slide_out_animation.setEasingCurve(
            EASING_FUNCTIONS.get(get_pr("close_animation_easing"), QEasingCurve.Linear)
        )

    def show_card(self):
        if self.slide_in_animation.state() == QPropertyAnimation.Running:
            self.slide_in_animation.stop()

        self.parent.timeline.start()
        self.parent.showing_card = True

        start_pos = QPoint(self.last_x, get_pr("start_y_pos"))
        end_pos = QPoint(get_pr("end_x_pos"), get_pr("end_y_pos"))

        self.slide_in_animation.setStartValue(start_pos)
        self.slide_in_animation.setEndValue(end_pos)
        self.slide_in_animation.start()

    def start_hide_card(self):
        if (
                self.parent.timeline.state() == QTimeLine.Running
                and self.parent.timeline.currentFrame() == 100
        ):
            self.hide_card()

    def hide_card(self):
        rect = self.parent.geometry()
        start_pos = QPoint(get_pr("end_x_pos"), get_pr("end_y_pos"))
        end_pos = QPoint(-rect.width(), get_pr("start_y_pos"))

        self.slide_out_animation.setStartValue(start_pos)
        self.slide_out_animation.setEndValue(end_pos)
        self.slide_out_animation.start()
        self.slide_out_animation.finished.connect(self.reset_card_properties)

    def reset_card_properties(self):
        # Reset card properties to avoid flickering or conflicts between animations
        self.parent.timeline.stop()
        self.parent.bar.setStyleSheet(f"background-color: {get_pr('custom_accent')};")
        self.parent.title_label.setText("")
        self.parent.artist_label.setText("")
        self.parent.img_label.clear()

        rect = self.parent.geometry()
        self.last_x = rect.x()

        self.parent.showing_card = False
        self.parent.updater.update_timer.start(1000)
