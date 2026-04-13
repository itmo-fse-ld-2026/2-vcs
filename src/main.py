from lib.ifmo import IFMOPortalClient
from lib.mapper.default import GraphMapper
from lib.asker import InteractiveAsker
from lib.primitives import User
import lib.config as config

if __name__ == "__main__":
  cfg = config.load()
  
  portal_client = IFMOPortalClient(cfg['variant'], cfg['base_url'])
  asker = InteractiveAsker()
  users = [User(name="Petya", email="petya@yandex.ru", id=0, branch=-1), User(name="Vasya", email="vasya@yandex.ru", id=1, branch=-1)]
  mapper = GraphMapper(portal_client, asker, users, cfg['cache_dir'])

  portal_client.clear_commit_area(cfg['cache_dir'])
  success, result, status = portal_client.get_branches()
  if success:
    mapper.map_json_to_graph(result)
  else:
    print(f"Error: {status} - {result}")