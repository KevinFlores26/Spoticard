import json, os
from typing import Any

class File:
  def load_json(self, file_path: str) -> dict[str | int, Any]:
    # Loads a JSON file and returns its key: value as a dictionary
    relative_path: str = self.get_relative_path(file_path)

    if os.path.exists(relative_path) and os.path.getsize(relative_path) > 0:
      with open(relative_path, "r") as f:
        data: dict[str | int, Any] = json.load(f)
        return data

    else:
      return { }

  @staticmethod
  def get_relative_path(file_path: str) -> str:
    # Get the path to the file relative to the project root
    project_root: str = os.path.dirname(os.path.dirname(__file__))
    relative_path: str = os.path.join(project_root, file_path)
    return relative_path
