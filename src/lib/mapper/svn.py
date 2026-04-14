import subprocess
import os
from typing import List, Optional
from lib.ifmo import IFMOPortalClient
from lib.primitives import User
from lib.asker import CLIAsker
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
    super().__init__(client, asker, users, ['.svn'], remote_subdir, local_subdir, diff_subdir)
    self.logger = logger
    self.repo_dir = f"{os.path.abspath(work_dir)}/.svn"
    self.repo_url = f"file://{self.repo_dir}"
    self.checkout_dir = os.path.join(work_dir, repo_subdir)
  
  def _execute_cmd(self, *args: str):
    self.logger.log(" ".join(args))
    return super()._execute_cmd(*args)

  def _svn(self, *args: str, cwd: Optional[str] = None):
    target_cwd = cwd or self.checkout_dir
    result = subprocess.run(
      ["svn", *args],
      cwd=target_cwd,
      capture_output=True,
      text=True
    )
    return result.stdout

  def _create_repo(self):
    os.makedirs(self.repo_dir, exist_ok=True)
    self.logger.log(f"mkdir -p {self.repo_dir}")

    subprocess.run(["svnadmin", "create", self.repo_dir])
    self.logger.log(f"svnadmin create {self.repo_dir}")

    os.makedirs(self.checkout_dir, exist_ok=True)
    self.logger.log(f"mkdir -p {self.checkout_dir}")

    subprocess.run(["svn", "checkout", "--username", self.current_user.name, self.repo_url, self.checkout_dir])
    self.logger.log(f"svn checkout --username {self.current_user.name} {self.repo_url} {self.checkout_dir}")

    self._svn("mkdir", "branches")
    self.logger.log(f"svn mkdir branches")

  def process_user_switch(self, user_id: int):
    self.current_user = self.users[user_id]

  def process_branch_create(self, branch_id: int, from_branch_id: Optional[int]) -> int:
    source = "trunk" if from_branch_id is None else f"branches/br-{from_branch_id}"
    target = f"branches/br-{branch_id}"
    self._svn("copy", f"{self.repo_url}/{source}", f"{self.repo_url}/{target}", "-m", f"Created {target}")
    self.logger.log(f"svn copy {self.repo_url}/{source} {self.repo_url}/{target} -m Created {target}")
    self._svn("update")
    self.logger.log(f"svn update")
    return branch_id

  def process_branch_switch(self, branch_id: int):
    target_path = f"{self.repo_url}/branches/br-{branch_id}"
    self._svn("switch", target_path)
    self.logger.log(f"svn switch {target_path}")

  def process_commit(self, commit_id: int, msg: str):
    self._svn("add", "--force", ".")
    self.logger.log(f"svn add --force .")
    full_msg = f"{msg}"
    self._svn("commit", "-m", full_msg, "--username", self.current_user.name)
    self.logger.log(f"svn commit -m {full_msg} --username {self.current_user.name}")

  def process_merge_commit(self, commit_id: int, from_branch_id: int, to_branch_id: int, msg: str):
    source_url = f"{self.repo_url}/branches/br-{from_branch_id}"
    self._svn("merge", source_url)
    self.logger.log(f"svn merge {source_url}")
    full_msg = f"{msg}"
    self._svn("commit", "-m", full_msg, "--username", self.current_user.name)
    self.logger.log(f"svn commit -m {full_msg} --username {self.current_user.name}")

  def map_json_to_graph(self, json_str: str):
    self.logger.clean()
    self.client.clear_commit_area(self.work_dir)
    self._create_repo()
    super().map_json_to_graph(json_str)