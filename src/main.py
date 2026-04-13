from lib.ifmo import IFMOPortalClient
from lib.graph import DefaultGraphClient
from lib.mapper import GraphMapper
from lib.asker import InteractiveAsker
from lib.primitives import User
import lib.config as config

if __name__ == "__main__":
  cfg = config.load()
  
  portal_client = IFMOPortalClient(cfg['variant'], cfg['base_url'])
  graph_client = DefaultGraphClient()
  asker = InteractiveAsker()
  users = [User(name="Petya", id=0, branch=-1), User(name="Vasya", id=1, branch=-1)]
  mapper = GraphMapper(graph_client, users)

  success, result, status = portal_client.get_branches()
  if success:
    mapper.map_json_to_graph(result)
    print(f"Graph loaded. Branches: {list(graph_client.branches.keys())}")
  else:
    print(f"Error: {status} - {result}")