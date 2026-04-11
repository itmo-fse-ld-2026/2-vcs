from lib.ifmo import IFMOPortalClient
from lib.graph import GraphClient
from lib.mapper import GraphMapper

if __name__ == "__main__":
  portal_client = IFMOPortalClient()
  graph_client = GraphClient()
  mapper = GraphMapper()

  success, result, status = portal_client.get_branches(variant=2)
  if success:
    mapper.map_json_to_graph(result, graph_client)
    print(f"Graph loaded. Branches: {list(graph_client.branches.keys())}")
  else:
    print(f"Error: {status} - {result}")

  success, result, status = portal_client.download_archive(variant=213, commit=4)
  if success:
    print(f"File saved: {result}")
  else:
    print(f"Error: {status} - {result}")