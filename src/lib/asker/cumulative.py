from typing import Dict, Optional
from lib.asker.default import CLIAsker

class CumulativeAsker:
  def __init__(self, base_asker: CLIAsker, messages: Dict[int, str]):
    self.base_asker = base_asker
    self.messages = messages

  def ask_commit_message(self, commit_id: int, prev_commit_id: Optional[int], diff_text: str) -> str:
    msg = self.base_asker.ask_commit_message(commit_id, prev_commit_id, diff_text)
    self.messages[commit_id] = msg
    return msg