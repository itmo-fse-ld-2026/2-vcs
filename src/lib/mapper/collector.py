from lib.mapper.default import GraphMapper
from typing import Optional, Dict

class CollectMessagesWrapper(GraphMapper):
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

  def process_branch_create(self, user_id: int, branch_id: int, from_branch_id: Optional[int]) -> int:
    return self.base_mapper.process_branch_create(user_id, branch_id, from_branch_id)

  def process_branch_switch(self, user_id: int, branch_id: int):
    self.base_mapper.process_branch_switch(user_id, branch_id)
  
  def process_pre_commit(self, commit_id: int, user_id: int):
    self.base_mapper.process_pre_commit(commit_id, user_id)

  def get_commit_message(self, commit_id: int) -> str:
    msg = self.base_mapper.get_commit_message(commit_id)
    self.messages[commit_id] = msg
    return msg

  def process_commit(self, user_id: int, commit_id: int, msg: str):
    self.base_mapper.process_commit(user_id, commit_id, msg)

  def process_merge_commit(self, user_id: int, commit_id: int, from_branch_id: int, to_branch_id: int, msg: str):
    self.base_mapper.process_merge_commit(user_id, commit_id, from_branch_id, to_branch_id, msg)
  
  def map_json_to_graph(self, json_str: str):
    self.base_mapper.map_json_to_graph(json_str)