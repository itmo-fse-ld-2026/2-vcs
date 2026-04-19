import os
from typing import List, Optional
from lib.ifmo import IFMOPortalClient
from lib.primitives import User
from lib.asker.default import CLIAsker
from lib.logger import Logger
from lib.mapper.default import GraphMapper

class SVNGraphMapper(GraphMapper):
  def __init__(self,
               client: IFMOPortalClient,
               asker: CLIAsker,
               users: List[User],
               logger: Logger,
               work_dir: str,
               remote_subdir: str = "remote",
               local_subdir: str = "local",
               diff_subdir: str = "diff_cache"):
    super().__init__(client, asker, users, [".svn"], work_dir, remote_subdir, local_subdir, diff_subdir)
    self.logger = logger
    self.remote_url = f"file://{self.remote_dir}"
  
  def _execute_cmd(self, args: List[str], output: bool=False, log: bool = True):
    if log:
      self.logger.log(" ".join(args))
    result = super()._execute_cmd(args)
    if output:
      decoded = result.stdout.decode('utf-8', errors='replace')
      for line in decoded.splitlines():
        self.logger.log(f"# {line}")
      decoded = result.stderr.decode('utf-8', errors='replace')
      for line in decoded.splitlines():
        self.logger.log(f"#! {line}")
    return result 

  def _svn(self, user_id: int, args: List[str], show_error: bool=True, output: bool=False) -> tuple[int, bytes]:
    result = self._execute_cmd(["svn", "--username", self.users[user_id].name, *args], output=output)
    if result.returncode != 0 and show_error:
      raise RuntimeError(f"Subversion Error: {result.stderr} | stdout: {result.stdout}")
    return (result.returncode, result.stdout)

  def init_repository(self):
    super().init_repository()
    self.logger.mark_section("structure")
    self._execute_cmd(["tree", "-dL", "1", self.work_dir], output=True)

    self.logger.mark_section("remote_configuration")
    result = self._execute_cmd(["svnadmin", "create", self.remote_dir])
    if result.returncode != 0:
      raise RuntimeError(f"Subversion Error: {result.stderr}")
    trunk_url = f"{self.remote_url}/trunk"
    self._svn(self.users[0].id, ["mkdir", trunk_url, "-m", f"\"create 'trunk' directory\""])
    self._svn(self.users[0].id, ["mkdir", f"{self.remote_url}/branches", "-m", f"\"create 'branches' directory\""])
    self.logger.mark_section("local_configuration")
    for user in self.users:
      user_path = os.path.join(self.local_dir, user.name)
      self._svn(user.id, ["checkout", trunk_url, user_path])
  
  def process_fetch(self, user_id: int):
    self.logger.increment_revision()
    username = self.users[user_id].name
    user_path = os.path.join(self.local_dir, username)
    self.logger.log("#bring changes from repository")
    self._svn(user_id, ["update", user_path])
  
  def process_push(self, user_id: int, branch_id: int):
    return super().process_push(user_id, branch_id)

  def process_branch_create(self, user_id: int, branch_id: int, from_branch_id: Optional[int]) -> int:
    branch_name = f"{self.remote_url}/branches/br-{branch_id}"
    if from_branch_id is None:
      self._svn(user_id, ["copy", f"{self.remote_url}/trunk", branch_name, "-m", f"\"create a new branch br-{branch_id}\""])
      return self.users[user_id].branch
    branch_source = f"{self.remote_url}/branches/br-{from_branch_id}"
    self._svn(user_id, ["copy", branch_source, branch_name, "-m", f"\"create a new branch br-{branch_id} from br-{from_branch_id}\""])
    return self.users[user_id].branch

  def process_branch_switch(self, user_id: int, branch_id: int):
    target_path = f"{self.remote_url}/branches/br-{branch_id}"
    user_path = os.path.join(self.local_dir, self.users[user_id].name)
    self.logger.log("#change local branch")
    self._svn(user_id, ["switch", target_path, user_path])

  def process_commit(self, user_id: int, commit_id: int, msg: str):
    user_path = os.path.join(self.local_dir, self.users[user_id].name)
    self.logger.log("#schedule addition of files if there are new ones")
    self._svn(user_id, ["add", "--force", user_path])
    self.logger.log("#svn has no property --allow-empty like git, so make it always have changes in metadata")
    self._svn(user_id, ["propset", "dummy-prop", f"r{commit_id}", user_path])
    self.logger.log("#save done changes on branch")
    self._svn(user_id, ["commit", "-m", f"\"{msg}\"", user_path])
  
  def _sync_changes(self, user_id: int, download_file: str, question_files: List[str]):
    self.logger.log("#sync changes with zip image")
    user_path = os.path.join(self.local_dir, self.users[user_id].name)
    user_dir = os.path.join(self.local_dir, self.users[user_id].name)
    for root, dirs, files in os.walk(user_path, topdown=True):
      if '.svn' in dirs:
        dirs.remove('.svn')
      
      for name in files + dirs:
        full_local_path = os.path.join(root, name)
        rel_path = os.path.relpath(full_local_path, user_path)
        archive_item_path = os.path.join(download_file, rel_path)
        
        is_protected = any(pattern in rel_path for pattern in self.vcs_protected)
        is_protected |= any(pattern in full_local_path for pattern in question_files)
        
        if not os.path.exists(archive_item_path) and not is_protected:
          self._svn(user_id, ["rm", "--force", full_local_path])

    contents = os.path.join(download_file, ".")
    cmd = ["rsync", "-av", "--checksum"]
    for pattern in self.vcs_protected:
        cmd.extend(["--exclude", pattern])
    cmd.extend([contents, user_dir])
    self._execute_cmd(cmd, output=True)

  def process_merge_commit(self, user_id: int, commit_id: int, from_branch_id: int, to_branch_id: int, msg: str):
    user_path = os.path.join(self.local_dir, self.users[user_id].name)
    source_url = f"{self.remote_url}/branches/br-{from_branch_id}"
    self.logger.log("#apply changes from different branch")
    error, _ = self._svn(user_id, ["merge", "--non-interactive", "--accept", "postpone", source_url, user_path], output=True, show_error=False)
    self.logger.log("#ensuring the current status")
    _, status_output = self._svn(user_id, ["status", user_path], output=True)
    status_text = status_output.decode('utf-8', errors='replace')
    lines = status_text.splitlines()
    has_conflict = any('C' in line[:7] for line in lines)
    question_files = [line.split(None, 1)[1] for line in lines if line.startswith('?')]
    success, file_path, _ = self.client.download_archive(commit_id, self.diff_dir)
    if not success:
      raise RuntimeError(f"Failed to download commit {commit_id}")
    if error != 0 or has_conflict:
      self._log_merge_conflicts(user_id, status_output.decode('utf-8', errors='replace'))
      self.logger.log("#having problems with merging, trying to solve them...")
      self.logger.log("#update dummy metadata to fix artificial merge conflicts, if any")
      self._svn(user_id, ["propset", "dummy-prop", f"r{commit_id}", user_path])
      self._log_resolved_conflicts(user_id, file_path)
      self._sync_changes(user_id, file_path, question_files)
      self.logger.log("#mark conflicts as resolved")
      self._svn(user_id, ["resolve", "--accept", "working", "-R", user_path])
    else:
      self._sync_changes(user_id, file_path, question_files)
    self.logger.log("#sync current state of files for committing (if during merge we decided to remove files)")
    self._svn(user_id, ["add", "--force", user_path])
    self.logger.log("#save done changes on branch")
    self._svn(user_id, ["commit", "-m", f'"{msg}"', user_path])
  
  def _get_conflicted_files(self, status_output: str) -> List[str]:
    conflicted_files: List[str] = []
    for line in status_output.splitlines():
      if line.startswith('C'):
        parts = line.split()
        if parts:
          conflicted_files.append(parts[-1])
    return conflicted_files
  
  def _get_metadata_conflict(self, status_output: str) -> List[str]:
    conflicting_meta: List[str] = []
    lines = status_output.splitlines()
    for line in lines:
      if len(line) > 1 and line[1] == 'C':
        path = line[7:].strip()
        prej_file = os.path.join(path, "dir_conflicts.prej")
        if os.path.exists(prej_file):
          try:
            with open(prej_file, 'r') as f:
              conflicting_meta.append(f.read())
          except Exception:
            pass
    return conflicting_meta
  
  def _log_merge_conflicts(self, user_id: int, status_output: str):
    self.logger.mark_conflict_revision()
    conflicting_metadata = self._get_metadata_conflict(status_output)
    if len(conflicting_metadata) > 0:
      self.logger.err(f"#viewing metadata conflicts")
      for meta in conflicting_metadata:
        if meta:
          self.logger.err(meta)
    conflicting_files = self._get_conflicted_files(status_output)
    for file in conflicting_files:
      if file:
        self.logger.err(f"#viewing conflicts of {file}")
        try:
          with open(file, 'r') as f:
            file_content = f.read()
        except UnicodeDecodeError:
          with open(file, 'rb') as f:
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