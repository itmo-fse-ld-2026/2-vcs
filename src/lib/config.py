import yaml
import os
from typing import Any, Dict

def load(file_path: str = "config.yaml") -> Dict[str, Any]:
  defaults: Dict[str, Any] = {
    "variant": 0,
    "base_url": "https://se.ifmo.ru/courses/software-engineering-basics",
    "output_dir": "./output",
    "git_dir": "git_project",
    "svn_dir": "svn_project",
    "git_log": "git.log",
    "svn_log": "svn.log",
    "vcs_plot": "plot.tex",
  }
  
  if not os.path.exists(file_path):
    print("Using default config.")
    return defaults

  try:
    with open(file_path, "r") as f:
      config = yaml.safe_load(f)
      return {**defaults, **(config or {})}
  except (yaml.YAMLError, IOError):
    return defaults