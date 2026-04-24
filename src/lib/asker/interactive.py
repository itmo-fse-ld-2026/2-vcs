from typing import Optional
import sys, os

class InteractiveAsker:
  def _clear_terminal(self):
    os.system('clear')

  def ask_commit_message(self, commit_id: int, prev_commit_id: Optional[int], diff_text: str) -> str:
    self._clear_terminal()
    if diff_text:
      if prev_commit_id is None:
        print(f"--- New for r{commit_id} ---")
      else:
        print(f"--- Diff for r{commit_id} vs r{prev_commit_id} ---")
      print(diff_text)
      print("-" * 30 + "\n")
    
    while True:
      try:
        msg = input(f"Enter commit message (r{commit_id}): ").strip()
        if not msg:
          return f"r{commit_id}"
        return f"r{commit_id}: {msg}"
      except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        sys.exit(0)
      except EOFError:
        print("\nInput stream closed.")
        sys.exit(1)
      except Exception as e:
        print(f"An unexpected error occurred: {e}")
        sys.exit(1)