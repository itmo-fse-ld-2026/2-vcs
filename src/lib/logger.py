from typing import Protocol

class Logger(Protocol):
  def clean(self):
    ...

  def log(self, message: str):
    ...
  
  def err(self, message: str):
    ...

  def increment_revision(self):
    ...
  
  def mark_section(self, section_name: str):
    ...
  
  def mark_err_section(self, section_name: str):
    ...
  
  def mark_conflict_revision(self):
    ...
  
  def mark_conflict_resolved(self):
    ...

class CommitLogger:
  def __init__(self, log_file: str, err_file: str, tag: str):
    self.log_file = log_file
    self.err_file = err_file
    self.tag = tag
    self.revision = 0
  
  def clean(self):
    open(self.log_file, "w").close()
    open(self.err_file, "w").close()

  def log(self, message: str):
    with open(self.log_file, "a") as f:
      f.write(f"{message}\n")
  
  def err(self, message: str):
    with open(self.err_file, "a") as f:
      f.write(f"{message}\n")

  def increment_revision(self):
    self.mark_section(f"revision_{self.revision}")
    self.revision += 1
  
  def mark_section(self, section_name: str):
    self.log(f"\n## {section_name}_{self.tag}")
  
  def mark_err_section(self, section_name: str):
    self.err(f"\n## {section_name}_{self.tag}")
  
  def mark_conflict_revision(self):
    self.mark_err_section(f"revision_{self.revision - 1}_conflict")
  
  def mark_conflict_resolved(self):
    self.mark_err_section(f"revision_{self.revision - 1}_resolved")