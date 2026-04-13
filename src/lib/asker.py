from typing import Protocol
import sys, os

class CLIAsker(Protocol):
  def ask_commit_message(self, commit_id: int, diff: str) -> str:
    ...

class InteractiveAsker:
  def _clear_terminal(self):
    os.system('clear')

  def ask_commit_message(self, commit_id: int, diff: str) -> str:
    self._clear_terminal()
    if diff:
      print(f"--- Diff for commit {commit_id} ---")
      print(diff)
      print("-" * 30 + "\n")
    
    while True:
      try:
        msg = input(f"Enter commit message (r{commit_id}): ").strip()
        if not msg:
          print("Error: Commit message cannot be empty.")
          continue
        return msg
      except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        sys.exit(0)
      except EOFError:
        print("\nInput stream closed.")
        sys.exit(1)
      except Exception as e:
        print(f"An unexpected error occurred: {e}")
        sys.exit(1)