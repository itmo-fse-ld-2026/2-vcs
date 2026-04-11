import json
from lib.asker import CLIAsker
from lib.graph import GraphClient
from lib.ifmo import IFMOPortalClient
from typing import Optional

class GraphMapper:
  @staticmethod
  def map_json_to_graph(json_str: str,
                        client: GraphClient,
                        work_dir: str,
                        asker: Optional[CLIAsker] = None,
                        portal_client: Optional[IFMOPortalClient] = None,
                        default_message: str = "Initial commit"):
    data = json.loads(json_str)
    sorted_branches = sorted(data.values(), key=lambda x: x["id"])

    for br_data in sorted_branches:
      source_name = None
      prev_commit_id = None

      if "parent" in br_data:
        source_name = br_data["parent"]["branch"]
        prev_commit_id = br_data["parent"]["commit"]
      
      branch = client.create_branch(
        name=br_data["name"],
        user_id=br_data["user"],
        source_branch_name=source_name
      )
      
      branch.id = br_data["id"]

      for c_id in br_data.get("commits", []):
        commit_id = int(c_id)
        diff_text = ""

        if asker and portal_client and prev_commit_id is not None:
          try:
            old_path = portal_client.get_commit_area(prev_commit_id, work_dir)
            new_path = portal_client.get_commit_area(commit_id, work_dir)
            diff_text = portal_client.get_diff(old_path, new_path)
          except Exception as e:
            diff_text = f"Could not generate diff: {e}"

        msg = default_message
        if asker:
          msg = asker.ask_commit_message(branch.name, commit_id, diff_text)
        
        client.add_commit(branch.name, commit_id, msg)
        prev_commit_id = commit_id

      if "merge" in br_data:
        client.merge_branches(
          source_name=br_data["merge"]["branch"],
          target_name=branch.name,
        )