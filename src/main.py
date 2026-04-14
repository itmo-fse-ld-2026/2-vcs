from lib.ifmo import IFMOPortalClient
from lib.mapper.git import GitGraphMapper
# from lib.mapper.svn import SVNGraphMapper
from lib.mapper.collector import CollectMessagesWrapper
# from lib.mapper.silence import SilentCommitMapper
from lib.asker import InteractiveAsker
from lib.primitives import User
from lib.logger import BasicLogger
from typing import Dict
import lib.config as config

if __name__ == "__main__":
  cfg = config.load()
  
  portal_client = IFMOPortalClient(cfg['variant'], cfg['base_url'])
  asker = InteractiveAsker()
  users = [User(name="Red", email="red@yandex.ru", id=0, branch=-1), User(name="Blue", email="blue@yandex.ru", id=1, branch=-1)]

  git_logger = BasicLogger(cfg['git_log'])
  svn_logger = BasicLogger(cfg['svn_log'])

  commit_messages: Dict[int, str] = dict()
  git_mapper = CollectMessagesWrapper(GitGraphMapper(portal_client, asker, users, git_logger, cfg['git_dir']), commit_messages)
  # svn_mapper = SilentCommitMapper(SVNGraphMapper(portal_client, asker, users, cfg['svn_dir']), commit_messages)

  success, result, status = portal_client.get_branches()
  if success:
    git_mapper.map_json_to_graph(result)
    # svn_mapper.map_json_to_graph(result)
  else:
    print(f"Error: {status} - {result}")