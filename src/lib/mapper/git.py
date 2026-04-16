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
  
  def _execute_cmd(self, args: List[str], output: bool=False, log: bool=True):
    if log:
      self.logger.log(" ".join(args))
    result = super()._execute_cmd(args)
    if output and result.stdout:
      decoded = result.stdout.decode('utf-8', errors='replace')
      for line in decoded.splitlines():
        self.logger.log(f"# {line}")
    if output and result.stderr:
      decoded = result.stdout.decode('utf-8', errors='replace')
      for line in decoded.splitlines():
        self.logger.log(f"#! {line}")
    return result 

  def _git(self, user_id: int, args: List[str], show_error: bool=True, output: bool=False) -> tuple[int, bytes]:
    user_path = os.path.join(self.local_dir, self.users[user_id].name)
    result = self._execute_cmd(["git", "-C", user_path, *args], output=output)
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
    self.logger.log("#save scheduled changes in the revision (even if nothing is changed)")
    self._git(user_id, ["commit", "--allow-empty", "-m", f"\"{msg}\""])

  def process_merge_commit(self, user_id: int, commit_id: int, from_branch_id: int, to_branch_id: int, msg: str):
    source_branch = f"br-{from_branch_id}"
    self.logger.log("#sync state of the desired branch with the remote repository")
    self._git(user_id, ["branch", "-f", source_branch, f"origin/{source_branch}"])
    self.logger.log("#apply changes from branch into single commit, preserving remote branch")
    error, _ = self._git(user_id, ["merge", source_branch, "--no-ff", "-m", f"\"{msg}\""], output=True, show_error=False)
    if error != 0:
      self._log_merge_conflicts(user_id)
      self.logger.log("#having problems with merging, trying to solve them...")
      user_dir = os.path.join(self.local_dir, self.users[user_id].name)
      success, file_path, _ = self.client.download_archive(commit_id, self.diff_dir)
      if not success:
        raise RuntimeError(f"Failed to download commit {commit_id}")
      self._log_resolved_conflicts(user_id, file_path)

      contents = os.path.join(file_path, ".")
      cmd = ["rsync", "-av", "--delete"]
      for pattern in self.vcs_protected:
          cmd.extend(["--exclude", pattern])
      cmd.extend([contents, user_dir])
      self._execute_cmd(cmd, output=True)
      self.process_commit(user_id, commit_id, msg)
  
  def _log_merge_conflicts(self, user_id: int):
    _, result = self._git(user_id, ["diff", "--name-only", "--diff-filter=U"], output=True)
    decoded_output = result.decode('utf-8', errors='replace')
    conflicting_files = decoded_output.strip().split('\n')
    self.logger.mark_conflict_revision()
    for file in conflicting_files:
      if file:
        abs_file = os.path.join(self.local_dir, self.users[user_id].name, file)
        self.logger.err(f"#viewing conflicts of {abs_file}")
        try:
          with open(abs_file, 'r') as f:
            file_content = f.read()
        except UnicodeDecodeError:
          with open(abs_file, 'rb') as f:
            file_content = f.read().decode('utf-8', errors='replace')
        if file_content:
          lines = file_content.split('\n')
          in_conflict = False
          conflict_block = []
          
          for i, line in enumerate(lines, 1):
            if line.startswith('<<<<<<<'):
              in_conflict = True
              conflict_block = [f"Line {i}: {line}"]
            elif line.startswith('=======') and in_conflict:
              conflict_block.append(f"Line {i}: {line}")
            elif line.startswith('>>>>>>>') and in_conflict:
              conflict_block.append(f"Line {i}: {line}")
              for conflict_line in conflict_block:
                self.logger.err(conflict_line)
              in_conflict = False
              conflict_block = []
            elif in_conflict:
              conflict_block.append(f"Line {i}: {line}")
  
  def _log_resolved_conflicts(self, user_id: int, archive_path: str):
    self.logger.mark_conflict_resolved()
    user_dir = os.path.join(self.local_dir, self.users[user_id].name)
    result = self._execute_cmd(
      ["diff", "-r", "-u", user_dir, archive_path],
      log=False
    )
    if result.stdout:
      decoded_output = result.stdout.decode('utf-8', errors='replace')
      for line in decoded_output.split('\n'):
        self.logger.err(f"# {line}")
    else:
      self.logger.err("#no differences with goal image are found")
  
  def process_pre_commit(self, commit_id: int, user_id: int):
    self.logger.log("#apply desired changes")
    return super().process_pre_commit(commit_id, user_id)

  def map_json_to_graph(self, json_str: str):
    self.logger.clean()
    self.client.clear_commit_area(self.work_dir)
    super().map_json_to_graph(json_str)