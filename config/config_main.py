import os, darkdetect
from typing import Union
from utils.helpers import load_json
from config.base import ConfigRelatedMeta

PrimitiveTypes = Union[str, int, bool]
PreferenceType = dict[str, PrimitiveTypes]
ThemesType = dict[str, dict[str, str]]


class Config(metaclass=ConfigRelatedMeta):
  def __init__(self):
    self.DEF_PREFS: PreferenceType = load_json(r"config\preferences_default.json")
    self.USER_PREFS: PreferenceType = load_json(r"config\preferences_user.json")
    self.THEMES: ThemesType = load_json(r"config\themes.json")
    self.NOWPLAYING_TXT_PATH: str = self.get_nowplaying_txt_path(self.USER_PREFS.get("nowplaying_txt_path", self.DEF_PREFS.get("nowplaying_txt_path")))

    self.current_theme_name: str = self.USER_PREFS.get("theme", self.DEF_PREFS.get("theme"))
    self.current_theme: dict[str, str] = { }

    self.set_current_theme(self.current_theme_name)

  def set_current_theme(self, theme_name: str = "") -> None:
    if theme_name == "":
      self.current_theme = self.USER_PREFS.get("theme", self.DEF_PREFS.get("theme"))
      return

    theme: dict[str, str] = self.THEMES.get(theme_name)
    if theme:
      self.current_theme = theme
      return

    # Adaptive theme as fallback
    if darkdetect.isDark():
      self.current_theme = self.THEMES.get("dark")
    else:
      self.current_theme = self.THEMES.get("light")

  def get_pr(self, key: str) -> PrimitiveTypes:
    preference: PrimitiveTypes = self.USER_PREFS.get(key, self.DEF_PREFS.get(key))
    return preference

  @staticmethod
  def get_nowplaying_txt_path(path: str = "") -> str:
    if path.startswith("C:\\"):
      return path

    username = os.getlogin()
    if not username:
      username = os.environ.get('USERNAME')

    if not path.endswith(".txt"):
      path += ".txt"

    return f"C:\\Users\\{username}\\AppData\\Roaming\\{path}"


# Singleton instance
config: Config = Config()
