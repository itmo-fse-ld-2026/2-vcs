from lib.primitives import Commit, Branch, Link
from typing import Dict, Optional

class GraphClient:
  def __init__(self):
    self.commits: Dict[int, Commit] = {}
    self.branches: Dict[str, Branch] = {}
    self._next_branch_id = 1

  def add_commit(self, branch_name: str, commit_id: int):
    if commit_id not in self.commits:
      self.commits[commit_id] = Commit(id=commit_id)
    
    if branch_name not in self.branches:
      raise ValueError(f"Branch {branch_name} does not exist.")
    
    self.branches[branch_name].commits.append(commit_id)

  def create_branch(self, name: str, user_id: int, source_branch_name: Optional[str] = None):
    parent_link = None
    if source_branch_name:
      source = self.branches.get(source_branch_name)
      if not source or not source.commits:
        raise ValueError("Source branch must exist and have at least one commit.")
      parent_link = Link(branch=source_branch_name, commit=source.commits[-1])

    new_branch = Branch(
      name=name,
      id=self._next_branch_id,
      user=user_id,
      commits=[],
      parent=parent_link
    )
    
    self.branches[name] = new_branch
    self._next_branch_id += 1
    return new_branch

  def merge_branches(self, source_name: str, target_name: str):
    source = self.branches.get(source_name)
    target = self.branches.get(target_name)

    if not source or not target:
      raise ValueError("Both branches must exist to merge.")
    
    if not source.commits:
      raise ValueError("Source branch has no commits to merge.")

    last_commit_id = source.commits[-1]
    target.merge = Link(branch=source_name, commit=last_commit_id)
    
    if last_commit_id not in target.commits:
      target.commits.append(last_commit_id)