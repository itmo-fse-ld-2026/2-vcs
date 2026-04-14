import subprocess
import os
from typing import List, Optional
from lib.ifmo import IFMOPortalClient
from lib.primitives import User
from lib.asker import CLIAsker
from lib.mapper.default import GraphMapper

class SVNGraphMapper(GraphMapper):
  def __init__(self, client: IFMOPortalClient, asker: CLIAsker, users: List[User], work_dir: str):
    super().__init__(client, asker, users, ['.svn'], work_dir)
    self.repo_url = f"file://{os.path.abspath(work_dir)}/repo"
    self.checkout_dir = os.path.join(work_dir, "checkout")
    self._ensure_repo_exists()

  def _svn(self, *args: str, cwd: Optional[str] = None):
    target_cwd = cwd or self.checkout_dir
    result = subprocess.run(
      ["svn", *args],
      cwd=target_cwd,
      capture_output=True,
      text=True
    )
    return result.stdout

  def _ensure_repo_exists(self):
    repo_path = self.repo_url.replace("file://", "")
    if not os.path.exists(repo_path):
      subprocess.run(["svnadmin", "create", repo_path])
      os.makedirs(self.checkout_dir, exist_ok=True)
      subprocess.run(["svn", "checkout", self.repo_url, self.checkout_dir])
      self._svn("mkdir", "trunk", "branches")
      self._svn("commit", "-m", "Initial structure")

  def process_user_switch(self, user_id: int):
    self.current_user = self.users[user_id]

  def process_branch_create(self, branch_id: int, from_branch_id: Optional[int]) -> int:
    source = "trunk" if from_branch_id is None else f"branches/br-{from_branch_id}"
    target = f"branches/br-{branch_id}"
    self._svn("copy", f"{self.repo_url}/{source}", f"{self.repo_url}/{target}", "-m", f"Created {target}")
    self._svn("update")
    return branch_id

  def process_branch_switch(self, branch_id: int):
    target_path = f"{self.repo_url}/branches/br-{branch_id}"
    self._svn("switch", target_path)

  def process_commit(self, commit_id: int, msg: str):
    self._svn("add", "--force", ".")
    full_msg = f"{msg}\n\nOriginal-ID: {commit_id}"
    self._svn("commit", "-m", full_msg, "--username", self.current_user.name)

  def process_merge_commit(self, commit_id: int, from_branch_id: int, to_branch_id: int, msg: str):
    source_url = f"{self.repo_url}/branches/br-{from_branch_id}"
    self._svn("merge", source_url)
    full_msg = f"{msg}\n\nMerge-ID: {commit_id}"
    self._svn("commit", "-m", full_msg, "--username", self.current_user.name)

  def map_json_to_graph(self, json_str: str):
    super().map_json_to_graph(json_str)