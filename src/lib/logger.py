from typing import Protocol

class Logger(Protocol):
  def clean(self):
    ...

  def log(self, message: str):
    ...

class BasicLogger:
  def __init__(self, filename: str):
    self.filename = filename
  
  def clean(self):
    open(self.filename, "w").close()

  def log(self, message: str):
    with open(self.filename, "a") as f:
      f.write(f"{message}\n")