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
  
  def _execute_cmd(self, args: List[str], output: bool=False):
    self.logger.log(" ".join(args))
    result = super()._execute_cmd(args)
    if output and result.stdout:
      for line in result.stdout.splitlines():
        self.logger.log(f"# {line}")
    if output and result.stderr:
      for line in result.stderr.splitlines():
        self.logger.log(f"#! {line}")
    return result 

  def _git(self, user_id: int, args: List[str], show_error: bool=True, output: bool=False) -> tuple[int, str]:
    user_path = os.path.join(self.local_dir, self.users[user_id].name)
    result = self._execute_cmd(["git", "-C", user_path, *args], output)
    if result.returncode != 0 and show_error:
      raise RuntimeError(f"Git Error: stderr: {result.stderr} | stdout: {result.stdout}")
    return (result.returncode, result.stdout)

  def init_repository(self):
    super().init_repository()
    self.logger.mark_section("structure")
    self._execute_cmd(["tree", "-dL", "1", self.work_dir], output=True)

    self.logger.mark_section("remote_configuration")
    result = self._execute_cmd(["git", "-C", self.remote_dir, "init", "--bare"])
    if result.returncode != 0:
      raise RuntimeError(f"Git Error: {result.stderr}")
    self.logger.mark_section("local_configuration")
    for user in self.users:
      self.logger.log("#create empty local repository")
      self._git(user.id, ["init"])
      self.logger.log("#specify user's name and email")
      self._git(user.id, ["config", "user.name", user.name])
      self._git(user.id, ["config", "user.email", user.email])
      self.logger.log("#specify remote repository address")
      self._git(user.id, ["remote", "add", "origin", self.remote_dir])
  
  def process_fetch(self, user_id: int):
    self.logger.increment_revision()
    self.logger.log("#receive updates from repository for remote branches")
    self._git(user_id, ["fetch", "origin"])
  
  def process_push(self, user_id: int, branch_id: int):
    branch_name = f"br-{branch_id}"
    self.logger.log("#send changes to the remote repository")
    self._git(user_id, ["push", "-u", "origin", branch_name])

  def process_branch_create(self, user_id: int, branch_id: int, from_branch_id: Optional[int]) -> int:
    branch_name = f"br-{branch_id}"
    if from_branch_id is None:
      self.logger.log("#rename current branch")
      self._git(user_id, ["branch", "-m", branch_name])
      return branch_id
    self.logger.log("#change to the desired branch (it may be mapped to the remote one)")
    self._git(user_id, ["switch", f"br-{from_branch_id}"])
    self.logger.log("#create a new branch from the specified branch")
    self._git(user_id, ["branch", branch_name, f"br-{from_branch_id}"])
    return from_branch_id

  def process_branch_switch(self, user_id: int, branch_id: int):
    branch_name = f"br-{branch_id}"
    self.logger.log("#change to the desired branch")
    self._git(user_id, ["switch", branch_name])

  def process_commit(self, user_id: int, commit_id: int, msg: str):
    self.logger.log("#schedule commiting all applied changes")
    self._git(user_id, ["add", "-A"])
    self.logger.log("#save scheduled changes in the revision")
    self._git(user_id, ["commit", "-m", f"\"{msg}\""])

  def process_merge_commit(self, user_id: int, commit_id: int, from_branch_id: int, to_branch_id: int, msg: str):
    source_branch = f"br-{from_branch_id}"
    self.logger.log("#sync state of the desired branch with the remote repository")
    self._git(user_id, ["branch", "-f", source_branch, f"origin/{source_branch}"])
    self.logger.log("#apply changes from branch into single commit, preserving remote branch")
    error, _ = self._git(user_id, ["merge", source_branch, "--no-ff", "-m", f"\"{msg}\""], output=True, show_error=False)
    if error != 0:
      self.logger.log("#having problems with merging, trying to solve them...")
      self.process_pre_commit(commit_id, user_id)
      self.process_commit(user_id, commit_id, msg)
  
  def process_pre_commit(self, commit_id: int, user_id: int):
    self.logger.log("#apply desired changes")
    return super().process_pre_commit(commit_id, user_id)

  def map_json_to_graph(self, json_str: str):
    self.logger.clean()
    self.client.clear_commit_area(self.work_dir)
    super().map_json_to_graph(json_str)