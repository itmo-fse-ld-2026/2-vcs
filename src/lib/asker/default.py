from typing import Protocol, Optional
import os

class CLIAsker(Protocol):
  def ask_commit_message(self, commit_id: int, prev_commit_id: Optional[int], diff_text: str) -> str:
    ...

class DefaultAsker:
  def _clear_terminal(self):
    os.system('clear')

  def ask_commit_message(self, commit_id: int, prev_commit_id: Optional[int], diff_text: str) -> str:
    print(f"Committing r{commit_id}...")
    return f"r{commit_id}"