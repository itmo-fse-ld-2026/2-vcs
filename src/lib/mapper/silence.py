from lib.mapper.default import GraphMapper
from typing import Optional, Dict

class SilentCommitMapper(GraphMapper):
  def __init__(self, base_mapper: GraphMapper, messages: Dict[int, str]):
    super().__init__(
      base_mapper.client, 
      base_mapper.asker, 
      base_mapper.users,
      base_mapper.vcs_protected,
      base_mapper.work_dir
    )
    self.base_mapper = base_mapper
    self.messages = messages

  def process_user_switch(self, user_id: int):
    self.base_mapper.process_user_switch(user_id)

  def process_branch_create(self, branch_id: int, from_branch_id: Optional[int]):
    self.base_mapper.process_branch_create(branch_id, from_branch_id)

  def process_branch_switch(self, branch_id: int):
    self.base_mapper.process_branch_switch(branch_id)
  
  def process_pre_commit(self, commit_id: int):
    self.base_mapper.process_pre_commit(commit_id)

  def get_commit_message(self, commit_id: int) -> str:
    msg = self.messages.get(commit_id)
    if msg is None:
      raise ValueError(f"Commit ID {commit_id} not found in mapping")
    return msg

  def process_commit(self, commit_id: int, msg: str):
    self.base_mapper.process_commit(commit_id, msg)

  def process_merge_commit(self, commit_id: int, from_branch_id: int, to_branch_id: int, msg: str):
    self.base_mapper.process_merge_commit(commit_id, from_branch_id, to_branch_id, msg)