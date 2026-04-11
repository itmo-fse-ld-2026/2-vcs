import yaml
import os
from typing import Any, Dict

def load(file_path: str = "config.yaml") -> Dict[str, Any]:
  defaults = {
    "variant": "0",
    "base_url": "https://se.ifmo.ru/courses/software-engineering-basics",
    "default_commit_message": "Automated commit",
    "work_dir": "diff_cache",
  }
  
  if not os.path.exists(file_path):
    return defaults

  try:
    with open(file_path, "r") as f:
      config = yaml.safe_load(f)
      return {**defaults, **(config or {})}
  except (yaml.YAMLError, IOError):
    return defaults