from lib.ifmo import IFMOPortalClient
from lib.graph import DefaultGraphClient
from lib.mapper import GraphMapper
from lib.asker import InteractiveAsker

if __name__ == "__main__":
  portal_client = IFMOPortalClient()
  graph_client = DefaultGraphClient()
  mapper = GraphMapper()
  asker = InteractiveAsker()

  success, result, status = portal_client.get_branches(variant=2)
  if success:
    mapper.map_json_to_graph(result, graph_client, asker)
    print(f"Graph loaded. Branches: {list(graph_client.branches.keys())}")
  else:
    print(f"Error: {status} - {result}")

  success, result, status = portal_client.download_archive(variant=213, commit=4)
  if success:
    print(f"File saved: {result}")
  else:
    print(f"Error: {status} - {result}")