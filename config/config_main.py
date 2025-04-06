import os, darkdetect
from itertools import cycle
from typing import Union
from utils.file_handling import File
from config.base import ConfigRelatedMeta

PrimitiveTypes = Union[str, int, bool]
PreferenceType = dict[str, PrimitiveTypes]
ThemesType = dict[str, dict[str, str]]

class Config(metaclass=ConfigRelatedMeta):
  def __init__(self):
    self.DEF_PREFS: PreferenceType = File().load_json(r"config\preferences_default.json")
    self.USER_PREFS: PreferenceType = File().load_json(r"config\preferences_user.json")
    self.THEMES: ThemesType = File().load_json(r"config\themes.json")
    self.THEME_NAMES: tuple[str, ...] = ("light", "dark", "user", "adaptive")

    self.NOWPLAYING_TXT_PATH: str = self.get_nowplaying_txt_path(self.USER_PREFS.get("nowplaying_txt_path", self.DEF_PREFS.get("nowplaying_txt_path")))
    self.is_nowplaying_txt_valid: bool = False

    # Theme-related Variables
    self.is_os_dark: bool = darkdetect.isDark()
    self.is_changing_theme: bool = False
    self.themes_cycle: cycle | None = None
    self.current_theme_name: str = self.USER_PREFS.get("theme", self.DEF_PREFS.get("theme"))
    self.current_theme: dict[str, str] = { }

    self.init_theme()

  def init_theme(self) -> None:
    # Initialize the themes cycle
    start_index: int = self.THEME_NAMES.index(self.current_theme_name)
    adapted_themes: tuple[str, ...] = self.THEME_NAMES[start_index:] + self.THEME_NAMES[:start_index]
    self.themes_cycle: cycle = cycle(adapted_themes)  # returns a cycle with the current theme at the start

    self.set_current_theme(next(self.themes_cycle), True)

  def set_current_theme(self, theme_name: str = "", initializing: bool = False) -> None:
    if not initializing:
      self.is_changing_theme = True

    theme: dict[str, str] = self.THEMES.get(theme_name)

    if not theme:
      self.switch_adaptive_theme()
      return

    self.current_theme_name = theme_name
    self.current_theme = theme

  def switch_adaptive_theme(self) -> None:
    is_dark: bool = darkdetect.isDark()

    self.is_os_dark = is_dark
    self.current_theme_name = "adaptive (dark)" if is_dark else "adaptive (light)"
    self.current_theme = self.THEMES.get("dark" if is_dark else "light")

  def get_pr(self, key: str) -> PrimitiveTypes:
    preference: PrimitiveTypes = self.USER_PREFS.get(key, self.DEF_PREFS.get(key))
    return preference

  @staticmethod
  def get_nowplaying_txt_path(path: str = "") -> str:
    if path.startswith("C:\\"):
      return path

    username: str = os.getlogin()
    if not username:
      username = os.environ.get('USERNAME')

    if not path.endswith(".txt"):
      path += ".txt"

    return f"C:\\Users\\{username}\\AppData\\Roaming\\{path}"


# Singleton instance
config: Config = Config()
