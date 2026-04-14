from typing import Protocol

class Logger(Protocol):
  def clean(self):
    ...

  def log(self, message: str):
    ...
  
  def increment_revision(self):
    ...

class CommitLogger:
  def __init__(self, filename: str):
    self.filename = filename
    self.revision = 0
  
  def clean(self):
    open(self.filename, "w").close()

  def log(self, message: str):
    with open(self.filename, "a") as f:
      f.write(f"{message}\n")
  
  def increment_revision(self):
    with open(self.filename, "a") as f:
      f.write(f"\n# Revision {self.revision}\n")
    self.revision += 1