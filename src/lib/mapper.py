import json
from typing import List, Set, Optional
from dataclasses import dataclass
from lib.graph import GraphClient
from lib.primitives import User

@dataclass
class CommitMeta:
  id: int
  branch_id: int
  user_id: int
  is_merge: bool
  is_first: bool
  from_branch_id: Optional[int]

class GraphMapper:
  def __init__(self, client: GraphClient, users: List[User]):
    self.client = client
    self.users = users
  
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
    commits = self._sort_commits(json_str)
    curr_user_idx = -1
    for c in commits:
      if c.user_id != curr_user_idx:
        curr_user_idx = c.user_id
        self.process_user_switch(c.user_id)
      if c.is_first:
        self.process_branch_create(c.branch_id, c.from_branch_id)
      if c.branch_id != self.users[c.user_id].branch:
        self.users[c.user_id].branch = c.branch_id
        self.process_branch_switch(c.branch_id)
      self.process_pre_commit()
      if c.is_merge:
        self.process_merge_commit(c.id, c.from_branch_id, c.branch_id)
      else:
        self.process_commit(c.id)
  
  def process_user_switch(self, user_id: int):
    print(f"Switching to user: {user_id}")
  
  def process_branch_create(self, branch_id: int, from_branch_id: Optional[int]):
    if from_branch_id is None:
      print(f"Creating branch: br-{branch_id}")
    else:
      print(f"Creating branch: br-{branch_id} from br-{from_branch_id}")
  
  def process_branch_switch(self, branch_id: int):
    print(f"Switching to branch: br-{branch_id}")
  
  def process_pre_commit(self):
    print("Pre commit actions.")
  
  def process_commit(self, commit_id: int):
    print(f"Doing commit r{commit_id}.")
  
  def process_merge_commit(self, commit_id: int, from_branch_id: int, to_branch_id: int):
    print(f"Doing merge commit r{commit_id}: br-{from_branch_id} -> br-{to_branch_id}")