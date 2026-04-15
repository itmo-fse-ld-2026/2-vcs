import json
import os
import subprocess
from typing import List, Set, Optional, Dict
from dataclasses import dataclass
from lib.ifmo import IFMOPortalClient
from lib.primitives import User
from lib.asker.default import CLIAsker

@dataclass
class CommitMeta:
  id: int
  branch_id: int
  user_id: int
  is_merge: bool
  is_first: bool
  from_branch_id: Optional[int]

class GraphMapper:
  def __init__(self,
               client: IFMOPortalClient,
               asker: CLIAsker,
               users: List[User],
               vcs_protected: List[str],
               work_dir: str,
               remote_subdir: str = "remote",
               local_subdir: str = "local",
               diff_subdir: str = "diff_cache"):
    self.client = client
    self.asker = asker
    self.users = users
    self.vcs_protected = vcs_protected
    self.work_dir = work_dir
    self.remote_dir = os.path.abspath(os.path.join(self.work_dir, remote_subdir))
    self.local_dir = os.path.join(self.work_dir, local_subdir)
    self.diff_dir = os.path.join(self.work_dir, diff_subdir)
  
  def _execute_cmd(self, args: List[str]):
    return subprocess.run(args, capture_output=True, text=True)
  
  def _sort_commits(self, json_str: str) -> List[CommitMeta]:
    data = json.loads(json_str)
    branches = {b["id"]: b for b in data.values()}
    name_to_id = {b["name"]: b["id"] for b in data.values()}
    
    processed_commits: Set[int] = set()
    started_branches: Set[int] = set()
    sorted_log: List[CommitMeta] = list()

    def process_branch(branch_id: int, until_commit: Optional[int] = None):
      branch = branches[branch_id]
      
      if "parent" in branch:
        p_info = branch["parent"]
        parent_id = name_to_id[p_info["branch"]]
        process_branch(parent_id, p_info["commit"])

      for c_id in branch["commits"]:
        if c_id in processed_commits:
          if c_id == until_commit: break
          continue

        is_merge = False
        from_br_id = None
        
        if "merge" in branch and branch["merge"]["commit"] == c_id:
          m_info = branch["merge"]
          merge_src_id = name_to_id[m_info["branch"]]
          process_branch(merge_src_id, m_info["commit"])
          is_merge = True
          from_br_id = merge_src_id

        is_first = False
        if branch_id not in started_branches:
          is_first = True
          started_branches.add(branch_id)
          if not is_merge and "parent" in branch:
            from_br_id = name_to_id[branch["parent"]["branch"]]

        sorted_log.append(CommitMeta(
          id=c_id, 
          branch_id=branch_id, 
          user_id=branch["user"], 
          is_merge=is_merge, 
          from_branch_id=from_br_id,
          is_first=is_first
        ))
        
        processed_commits.add(c_id)
        if c_id == until_commit:
          break

    for b_id in sorted(branches.keys()):
      process_branch(b_id)
      
    return sorted(sorted_log, key=lambda x: x.id)

  def map_json_to_graph(self, json_str: str):
    self.init_repository()
    commits = self._sort_commits(json_str)
    branch_heads: Dict[int, int] = {}
    for c in commits:
      self.process_fetch(c.user_id)
      if c.is_first:
        self.users[c.user_id].branch = self.process_branch_create(c.user_id, c.branch_id, c.from_branch_id)
        if c.from_branch_id is not None and c.from_branch_id in branch_heads:
          branch_heads[c.branch_id] = branch_heads[c.from_branch_id]
      if c.branch_id != self.users[c.user_id].branch:
        self.users[c.user_id].branch = c.branch_id
        self.process_branch_switch(c.user_id, c.branch_id)
      self.process_pre_commit(c.id, c.user_id)
      prev_commit_id = branch_heads.get(c.branch_id)
      commit_message = self.get_commit_message(c.id, prev_commit_id)
      if c.is_merge and c.from_branch_id is not None:
        self.process_merge_commit(c.user_id, c.id, c.from_branch_id, c.branch_id, commit_message)
      else:
        self.process_commit(c.user_id, c.id, commit_message)
      branch_heads[c.branch_id] = c.id
      self.process_push(c.user_id, c.branch_id)
  
  def init_repository(self):
    self._execute_cmd(["mkdir", "-p", self.work_dir, self.remote_dir, self.local_dir, os.path.join(self.diff_dir, "empty")])
    for user in self.users:
      user_path = os.path.join(self.local_dir, user.name)
      self._execute_cmd(["mkdir", "-p", user_path])
  
  def process_fetch(self, user_id: int):
    pass

  def process_push(self, user_id: int, branch_id: int):
    pass
  
  def process_branch_create(self, user_id: int, branch_id: int, from_branch_id: Optional[int]) -> int:
    if from_branch_id is None:
      print(f"Creating branch: br-{branch_id}")
    else:
      print(f"Creating branch: br-{branch_id} from br-{from_branch_id}")
    return branch_id
  
  def process_branch_switch(self, user_id: int, branch_id: int):
    print(f"Switching to branch: br-{branch_id}")
  
  def process_pre_commit(self, commit_id: int, user_id: int):
    user_dir = os.path.join(self.local_dir, self.users[user_id].name)
    for item in os.listdir(user_dir):
      if item in self.vcs_protected:
        continue
      
      item_path = os.path.join(user_dir, item)
      self._execute_cmd(["rm", "-rf", item_path])

    success, file_path, _ = self.client.download_archive(commit_id, self.diff_dir)
    if not success:
      raise RuntimeError(f"Failed to download commit {commit_id}")

    result = self._execute_cmd(["unzip", "-q", file_path, "-d", user_dir])

    if result.returncode != 0:
      if not os.path.exists(self.local_dir) or not os.listdir(self.local_dir):
        raise RuntimeError(f"Unzip failed: {result.stderr}")

    self._execute_cmd(["rm", "-f", file_path])
  
  def get_commit_message(self, commit_id: int, prev_commit_id: Optional[int]) -> str:
    new_path = self.client.get_commit_area(commit_id, self.work_dir)
    if prev_commit_id is not None:
      old_path = self.client.get_commit_area(prev_commit_id, self.work_dir)
    else:
      old_path = os.path.join(self.diff_dir, "empty")
    diff_text = self.client.get_diff(old_path, new_path)
    return self.asker.ask_commit_message(commit_id, prev_commit_id, diff_text)
  
  def process_commit(self, user_id: int, commit_id: int, msg: str):
    print(f"Doing commit r{commit_id}.")
    print(f"msg: {msg}")
  
  def process_merge_commit(self, user_id: int, commit_id: int, from_branch_id: int, to_branch_id: int, msg: str):
    print(f"Doing merge commit r{commit_id}: br-{from_branch_id} -> br-{to_branch_id}")
    print(f"msg: {msg}")