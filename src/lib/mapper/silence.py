from lib.mapper.default import GraphMapper
from typing import Optional

class SilentCommitMapper(GraphMapper):
  def __init__(self, base_mapper: GraphMapper, silent_id: int, silent_msg: str):
    self.base_mapper = base_mapper
    self.silent_id = silent_id
    self.silent_msg = silent_msg
    self.client = base_mapper.client
    self.asker = base_mapper.asker
    self.users = base_mapper.users
    self.work_dir = base_mapper.work_dir

  def process_user_switch(self, user_id: int):
    self.base_mapper.process_user_switch(user_id)

  def process_branch_create(self, branch_id: int, from_branch_id: Optional[int]):
    self.base_mapper.process_branch_create(branch_id, from_branch_id)

  def process_branch_switch(self, branch_id: int):
    self.base_mapper.process_branch_switch(branch_id)

  def process_pre_commit(self, commit_id: int) -> str:
    if commit_id == self.silent_id:
      return self.silent_msg
    return self.base_mapper.process_pre_commit(commit_id)

  def process_commit(self, commit_id: int, msg: str):
    self.base_mapper.process_commit(commit_id, msg)

  def process_merge_commit(self, commit_id: int, from_branch_id: int, to_branch_id: int, msg: str):
    self.base_mapper.process_merge_commit(commit_id, from_branch_id, to_branch_id, msg)