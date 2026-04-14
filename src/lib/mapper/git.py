import subprocess
import os
from typing import List, Optional
from lib.ifmo import IFMOPortalClient
from lib.primitives import User
from lib.asker import CLIAsker
from lib.mapper.default import GraphMapper
from lib.logger import Logger

class GitGraphMapper(GraphMapper):
  def __init__(self, client: IFMOPortalClient, asker: CLIAsker, users: List[User], logger: Logger, work_dir: str, repo_subdir: str = "repo"):
    super().__init__(client, asker, users, ['.git'], work_dir, repo_subdir)
    self.logger = logger

  def _git(self, *args: str):
    result = subprocess.run(
      ["git", "-C", self.repo_dir, *args],
      capture_output=True,
      text=True
    )
    if result.returncode != 0:
      print(f"Git Error: {result.stderr}")
    return result.stdout

  def _create_repo(self):
    os.makedirs(self.repo_dir, exist_ok=True)
    self.logger.log(f"mkdir -p {self.repo_dir}")
    self._git("init")
    self.logger.log(f"git init")

  def process_user_switch(self, user_id: int):
    user = self.users[user_id]
    self._git("config", "user.name", user.name)
    self._git("config", "user.email", user.email)
    self.logger.log(f"git config user.name {user.name}")
    self.logger.log(f"git config user.email {user.email}")

  def process_branch_create(self, branch_id: int, from_branch_id: Optional[int]) -> int:
    branch_name = f"br-{branch_id}"
    if from_branch_id is None:
      self._git("branch", "-m", branch_name)
      self.logger.log(f"git branch -m {branch_name}")
      return branch_id
    else:
      self._git("branch", branch_name, f"br-{from_branch_id}")
      self.logger.log(f"git branch {branch_name} br-{from_branch_id}")
      return from_branch_id

  def process_branch_switch(self, branch_id: int):
    branch_name = f"br-{branch_id}"
    self._git("switch", branch_name)
    self.logger.log(f"git switch {branch_name}")

  def process_commit(self, commit_id: int, msg: str):
    self._git("add", "-A")
    self.logger.log(f"git add -A")
    full_msg = f"{msg}\n\nOriginal-ID: {commit_id}"
    self._git("commit", "-m", full_msg)
    self.logger.log(f"git commit -m {full_msg}")

  def process_merge_commit(self, commit_id: int, from_branch_id: int, to_branch_id: int, msg: str):
    source_branch = f"br-{from_branch_id}"
    self._git("merge", source_branch, "--no-ff", "-m", f"{msg}\n\nMerge-ID: {commit_id}")
    self.logger.log(f"git merge {source_branch} --no-ff -m {msg}\n\nMerge-ID: {commit_id}")
    self._git("add", "-A")
    self.logger.log(f"git add -A")

  def map_json_to_graph(self, json_str: str):
    self.logger.clean()
    self.client.clear_commit_area(self.work_dir)
    self._create_repo()
    super().map_json_to_graph(json_str)