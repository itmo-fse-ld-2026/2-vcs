from lib.ifmo import IFMOPortalClient
from lib.mapper.git import GitGraphMapper
from lib.mapper.svn import SVNGraphMapper
from lib.asker.default import InteractiveAsker
from lib.asker.silent import SilentAsker
from lib.asker.cumulative import CumulativeAsker
from lib.primitives import User
from lib.logger import CommitLogger
from lib.plot import DefaultPlotter
from typing import Dict
import lib.config as config
import os
import subprocess

if __name__ == "__main__":
  cfg = config.load()
  
  portal_client = IFMOPortalClient(cfg['variant'], cfg['base_url'])

  commit_messages: Dict[int, str] = dict()
  asker = InteractiveAsker()
  silent_asker = SilentAsker(commit_messages)
  cumulative_asker = CumulativeAsker(asker, commit_messages)
  users = [User(name="Red", email="red@yandex.ru", id=0, branch=-1), User(name="Blue", email="blue@yandex.ru", id=1, branch=-1)]

  out_dir: str = cfg['output_dir']
  if os.path.exists(out_dir):
    subprocess.run(["rm", "-rf", out_dir])
  os.makedirs(out_dir)

  git_log: str = os.path.join(out_dir, cfg['git_log'])
  svn_log: str = os.path.join(out_dir, cfg['svn_log'])
  git_logger = CommitLogger(git_log)
  svn_logger = CommitLogger(svn_log)

  git_dir: str = os.path.join(out_dir, cfg['git_dir'])
  svn_dir: str = os.path.join(out_dir, cfg['svn_dir'])
  git_mapper = GitGraphMapper(portal_client, cumulative_asker, users, git_logger, git_dir)
  svn_mapper = SVNGraphMapper(portal_client, silent_asker, users, svn_logger, svn_dir)

  plotter = DefaultPlotter(
    {0: "red", 1: "blue"},
    0.5, 0.5, 0.5, 0.5
  )

  vcs_plot: str = os.path.join(out_dir, cfg['vcs_plot'])
  success, result, status = portal_client.get_branches()
  if success:
    vcs_plot_data = plotter.generate_script(result)
    with open(vcs_plot, 'w') as f:
      f.write(vcs_plot_data)
    git_mapper.map_json_to_graph(result)
    svn_mapper.map_json_to_graph(result)
  else:
    print(f"Error: {status} - {result}")