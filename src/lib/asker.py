from typing import Protocol

class CLIAsker(Protocol):
  def ask_commit_message(self, branch_name: str, commit_id: int) -> str:
    ...

class InteractiveAsker:
  def ask_commit_message(self, branch_name: str, commit_id: int) -> str:
    print(f"\nBranch: {branch_name} | Commit ID: {commit_id}")
    msg = input("Enter commit message: ").strip()
    return msg if msg else f"Auto-generated for {commit_id}"