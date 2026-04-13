import subprocess
import os
from typing import List, Optional
from lib.ifmo import IFMOPortalClient
from lib.primitives import User
from lib.asker import CLIAsker
from lib.mapper.default import GraphMapper

class GitGraphMapper(GraphMapper):
  def __init__(self, client: IFMOPortalClient, asker: CLIAsker, users: List[User], work_dir: str):
    super().__init__(client, asker, users, work_dir)
    self._ensure_repo_exists()

  def _git(self, *args: str):
    result = subprocess.run(
      ["git", "-C", self.work_dir, *args],
      capture_output=True,
      text=True
    )
    if result.returncode != 0:
      print(f"Git Error: {result.stderr}")
    return result.stdout

  def _ensure_repo_exists(self):
    if not os.path.exists(os.path.join(self.work_dir, ".git")):
      subprocess.run(["git", "init", self.work_dir])

  def process_user_switch(self, user_id: int):
    user = self.users[user_id]
    self._git("config", "user.name", user.name)
    self._git("config", "user.email", user.email)

  def process_branch_create(self, branch_id: int, from_branch_id: Optional[int]):
    branch_name = f"br-{branch_id}"
    if from_branch_id is None:
      self._git("checkout", "-b", branch_name)
    else:
      self._git("branch", branch_name, f"br-{from_branch_id}")

  def process_branch_switch(self, branch_id: int):
    branch_name = f"br-{branch_id}"
    self._git("checkout", branch_name)

  def process_commit(self, commit_id: int, msg: str):
    self._git("add", "-A")
    full_msg = f"{msg}\n\nOriginal-ID: {commit_id}"
    self._git("commit", "-m", full_msg)

  def process_merge_commit(self, commit_id: int, from_branch_id: int, to_branch_id: int, msg: str):
    source_branch = f"br-{from_branch_id}"
    self._git("merge", source_branch, "--no-ff", "-m", f"{msg}\n\nMerge-ID: {commit_id}")
    self._git("add", "-A")

  def map_json_to_graph(self, json_str: str):
    super().map_json_to_graph(json_str)