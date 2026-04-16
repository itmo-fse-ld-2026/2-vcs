from typing import Protocol

class Logger(Protocol):
  def clean(self):
    ...

  def log(self, message: str):
    ...

  def increment_revision(self):
    ...
  
  def mark_section(self, section_name: str):
    ...

class CommitLogger:
  def __init__(self, filename: str, tag: str):
    self.filename = filename
    self.tag = tag
    self.revision = 0
  
  def clean(self):
    open(self.filename, "w").close()

  def log(self, message: str):
    with open(self.filename, "a") as f:
      f.write(f"{message}\n")
  
  def increment_revision(self):
    self.mark_section(f"revision_{self.revision}")
    self.revision += 1
  
  def mark_section(self, section_name: str):
    with open(self.filename, "a") as f:
      f.write(f"\n## {section_name}_{self.tag}\n")