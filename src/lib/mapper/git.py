import os
from typing import List, Optional
from lib.ifmo import IFMOPortalClient
from lib.primitives import User
from lib.asker.default import CLIAsker
from lib.mapper.default import GraphMapper
from lib.logger import Logger

class GitGraphMapper(GraphMapper):
  def __init__(self,
               client: IFMOPortalClient,
               asker: CLIAsker,
               users: List[User],
               logger: Logger,
               work_dir: str,
               remote_subdir: str = "remote",
               local_subdir: str = "local",
               diff_subdir: str = "diff_cache"):
    super().__init__(client, asker, users, ['.git'], work_dir, remote_subdir, local_subdir, diff_subdir)
    self.logger = logger
  
  def _execute_cmd(self, *args: str):
    self.logger.log(" ".join(args))
    return super()._execute_cmd(*args)

  def _git(self, user_id: int, *args: str):
    user_path = os.path.join(self.local_dir, self.users[user_id].name)
    result = self._execute_cmd("git", "-C", user_path, *args)
    if result.returncode != 0:
      raise RuntimeError(f"Git Error: {result.stderr}")
    return result.stdout

  def init_repository(self):
    super().init_repository()
    result = self._execute_cmd("git", "-C", self.remote_dir, "init", "--bare")
    if result.returncode != 0:
      raise RuntimeError(f"Git Error: {result.stderr}")
    for user in self.users:
      self._git(user.id, "init")
      self._git(user.id, "config", "user.name", user.name)
      self._git(user.id, "config", "user.email", user.email)
      self._git(user.id, "remote", "add", "origin", self.remote_dir)
  
  def process_fetch(self, user_id: int):
    self.logger.increment_revision()
    self._git(user_id, "fetch", "origin")
  
  def process_push(self, user_id: int, branch_id: int):
    branch_name = f"br-{branch_id}"
    self._git(user_id, "push", "-u", "origin", branch_name)

  def process_branch_create(self, user_id: int, branch_id: int, from_branch_id: Optional[int]) -> int:
    branch_name = f"br-{branch_id}"
    if from_branch_id is None:
      self._git(user_id, "branch", "-m", branch_name)
      return branch_id
    self._git(user_id, "switch", f"br-{from_branch_id}")
    self._git(user_id, "branch", branch_name, f"br-{from_branch_id}")
    return from_branch_id

  def process_branch_switch(self, user_id: int, branch_id: int):
    branch_name = f"br-{branch_id}"
    self._git(user_id, "switch", branch_name)

  def process_commit(self, user_id: int, commit_id: int, msg: str):
    self._git(user_id, "add", "-A")
    self._git(user_id, "commit", "-m", msg)

  def process_merge_commit(self, user_id: int, commit_id: int, from_branch_id: int, to_branch_id: int, msg: str):
    source_branch = f"br-{from_branch_id}"
    self._git(user_id, "merge", source_branch, "--no-ff", "-m", f"{msg}")
    self._git(user_id, "add", "-A")

  def map_json_to_graph(self, json_str: str):
    self.logger.clean()
    self.client.clear_commit_area(self.work_dir)
    super().map_json_to_graph(json_str)