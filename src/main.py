from lib.ifmo import IFMOPortalClient
from lib.graph import DefaultGraphClient
from lib.mapper import GraphMapper
from lib.asker import InteractiveAsker
import lib.config as config

if __name__ == "__main__":
  cfg = config.load()
  
  portal_client = IFMOPortalClient(cfg['variant'], cfg['base_url'])
  graph_client = DefaultGraphClient()
  mapper = GraphMapper()
  asker = InteractiveAsker()

  success, result, status = portal_client.get_branches()
  if success:
    mapper.map_json_to_graph(result, graph_client, cfg['work_dir'], asker, portal_client)
    print(f"Graph loaded. Branches: {list(graph_client.branches.keys())}")
  else:
    print(f"Error: {status} - {result}")