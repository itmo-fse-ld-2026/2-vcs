import json
from lib.graph import GraphClient

class GraphMapper:
  @staticmethod
  def map_json_to_graph(json_str: str, client: GraphClient):
    data = json.loads(json_str)
    
    sorted_branches = sorted(data.values(), key=lambda x: x["id"])

    for br_data in sorted_branches:
      source_name = None
      if "parent" in br_data:
        source_name = br_data["parent"]["branch"]
      
      branch = client.create_branch(
        name=br_data["name"],
        user_id=br_data["user"],
        source_branch_name=source_name
      )
      
      branch.id = br_data["id"]

      for c_id in br_data.get("commits", []):
        client.add_commit(branch.name, c_id)

      if "merge" in br_data:
        client.merge_branches(
          source_name=br_data["merge"]["branch"],
          target_name=branch.name,
        )