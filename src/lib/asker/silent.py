from typing import Dict, Optional

class SilentAsker:
  def __init__(self, messages: Dict[int, str]):
    self.messages = messages

  def ask_commit_message(self, commit_id: int, prev_commit_id: Optional[int], diff_text: str) -> str:
    print(f"Committing r{commit_id} silently...")
    msg = self.messages.get(commit_id)
    if msg is None:
      raise ValueError(f"Commit ID {commit_id} not found in mapping")
    return msg