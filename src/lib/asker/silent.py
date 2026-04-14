from typing import Dict

class SilentAsker:
  def __init__(self, messages: Dict[int, str]):
    self.messages = messages

  def ask_commit_message(self, commit_id: int, diff_text: str) -> str:
    msg = self.messages.get(commit_id)
    if msg is None:
      raise ValueError(f"Commit ID {commit_id} not found in mapping")
    return msg