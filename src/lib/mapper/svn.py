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
  
  def _execute_cmd(self, *args: str):
    self.logger.log(" ".join(args))
    return super()._execute_cmd(*args)

  def _svn(self, user_id: int, *args: str):
    result = self._execute_cmd("svn", "--username", self.users[user_id].name, *args)
    if result.returncode != 0:
      raise RuntimeError(f"Subversion Error: {result.stderr}")
    return result.stdout

  def init_repository(self):
    super().init_repository()
    result = self._execute_cmd("svnadmin", "create", self.remote_dir)
    if result.returncode != 0:
      raise RuntimeError(f"Subversion Error: {result.stderr}")
    trunk_url = f"{self.remote_url}/trunk"
    self._svn(self.users[0].id, "mkdir", trunk_url, "-m", f"\"create 'trunk' directory\"")
    self._svn(self.users[0].id, "mkdir", f"{self.remote_url}/branches", "-m", f"\"create 'branches' directory\"")
    for user in self.users:
      user_path = os.path.join(self.local_dir, user.name)
      self._svn(user.id, "checkout", trunk_url, user_path)
      # self._svn("mkdir", "branches")
  
  def process_fetch(self, user_id: int):
    self.logger.increment_revision()
    username = self.users[user_id].name
    user_path = os.path.join(self.local_dir, username)
    self._svn(user_id, "update", user_path)
  
  def process_push(self, user_id: int, branch_id: int):
    return super().process_push(user_id, branch_id)

  def process_branch_create(self, user_id: int, branch_id: int, from_branch_id: Optional[int]) -> int:
    branch_name = f"{self.remote_url}/branches/br-{branch_id}"
    if from_branch_id is None:
      self._svn(user_id, "copy", f"{self.remote_url}/trunk", branch_name, "-m", f"\"create a new branch br-{branch_id}\"")
      return self.users[user_id].branch
    branch_source = f"{self.remote_url}/branches/br-{from_branch_id}"
    self._svn(user_id, "copy", branch_source, branch_name, "-m", f"create a new branch br-{branch_id} from br-{from_branch_id}")
    return branch_id

  def process_branch_switch(self, user_id: int, branch_id: int):
    target_path = f"{self.remote_url}/branches/br-{branch_id}"
    user_path = os.path.join(self.local_dir, self.users[user_id].name)
    self._svn(user_id, "switch", target_path, user_path)

  def process_commit(self, user_id: int, commit_id: int, msg: str):
    user_path = os.path.join(self.local_dir, self.users[user_id].name)
    self._svn(user_id, "add", "--force", user_path)
    self._svn(user_id, "commit", "-m", msg, user_path)

  def process_merge_commit(self, user_id: int, commit_id: int, from_branch_id: int, to_branch_id: int, msg: str):
    source_url = f"{self.remote_url}/branches/br-{from_branch_id}"
    self._svn(user_id, "merge", source_url)
    self._svn(user_id, "commit", "-m", msg, )

  def map_json_to_graph(self, json_str: str):
    self.logger.clean()
    self.client.clear_commit_area(self.work_dir)
    super().map_json_to_graph(json_str)