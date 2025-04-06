import keyboard
from PyQt5 import QtWidgets
from config.auth_config import sp_auth
from config.config_main import config
from ui.music_card.window import MusicCardWindow

# Run the app
if __name__ == "__main__":
  app = QtWidgets.QApplication([])
  card_window = MusicCardWindow(app)

  # Add shortcut listeners
  if config.get_pr("shortcuts"):
    def check(shortcut, check_scope=False):
      is_string = lambda shortcut: isinstance(shortcut, str)
      if check_scope:
        return (
          config.get_pr(f"{shortcut}_shortcut") and
          is_string(config.get_pr(f"{shortcut}_shortcut")) and
          "user-modify-playback-state" in sp_auth.PARAMS["SCOPE"]
        )

      return config.get_pr(f"{shortcut}_shortcut") and is_string(config.get_pr(f"{shortcut}_shortcut"))


    if check("visibility"):
      keyboard.add_hotkey(config.get_pr("visibility_shortcut"), lambda: card_window.visibility_listener.emit())
    if check("theme"):
      keyboard.add_hotkey(config.get_pr("theme_shortcut"), lambda: card_window.theme_listener.emit())

    if check("play_pause", True):
      keyboard.add_hotkey(config.get_pr("play_pause_shortcut"), lambda: card_window.play_pause_listener.emit())
    if check("next", True):
      keyboard.add_hotkey(config.get_pr("next_shortcut"), lambda: card_window.next_listener.emit())
    if check("previous", True):
      keyboard.add_hotkey(config.get_pr("previous_shortcut"), lambda: card_window.previous_listener.emit())
    if check("shuffle", True):
      keyboard.add_hotkey(config.get_pr("shuffle_shortcut"), lambda: card_window.shuffle_listener.emit())
    if check("repeat", True):
      keyboard.add_hotkey(config.get_pr("repeat_shortcut"), lambda: card_window.repeat_listener.emit())
    if check("volume_up", True):
      keyboard.add_hotkey(config.get_pr("volume_up_shortcut"), lambda: card_window.volume_up_listener.emit())
    if check("volume_down", True):
      keyboard.add_hotkey(config.get_pr("volume_down_shortcut"), lambda: card_window.volume_down_listener.emit())

    if check("snooze"):
      keyboard.add_hotkey(config.get_pr("snooze_shortcut"), lambda: card_window.snooze_listener.emit())
    if check("exit"):
      keyboard.add_hotkey(config.get_pr("exit_shortcut"), lambda: card_window.exit_listener.emit())

  card_window.show()
  app.exec_()
