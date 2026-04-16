import os
import re
from typing import Dict, Set, List
from jinja2 import Environment, FileSystemLoader, meta

class ReportFiller:
  def __init__(self, context: Dict[str, str], report_dir: str):
    self.context: Dict[str, str] = context
    self.report_dir = report_dir
    self.env = Environment(loader=FileSystemLoader(report_dir))
    self.section_regex = re.compile(r"## (.+)\n([\s\S]*?)(?=\n## |$)")

  def parse_artifact(self, artifact_path: str):
    if not os.path.exists(artifact_path):
      raise FileNotFoundError(f"Artifact not found: {artifact_path}")
    
    try:
      with open(artifact_path, "r") as f:
        content = f.read()
      
      sections = self.section_regex.findall(content)
      
      if not sections:
        return
      
      for name, body in sections:
        self.context[name.strip()] = body.strip()
    except IOError as e:
      raise RuntimeError(f"Error reading artifact: {e}")

  def compile_patterns(self):
    if not os.path.isdir(self.report_dir):
      raise NotADirectoryError(f"Invalid report directory: {self.report_dir}")
    
    self._render_revision_summary()

    self.env.loader = FileSystemLoader(self.report_dir)

    for root, _, files in os.walk(self.report_dir):
      for filename in files:
        if filename.endswith(".jinja"):
          rel_path = os.path.relpath(os.path.join(root, filename), self.report_dir)
          output_path = os.path.join(self.report_dir, rel_path).replace(".jinja", ".tex")
          
          rendered_content = self._render_template(rel_path)
          
          os.makedirs(os.path.dirname(output_path), exist_ok=True)
          with open(output_path, "w") as f:
            f.write(rendered_content)
  
  def _render_revision_summary(self):
    git_revisions: Set[int] = set()
    svn_revisions: Set[int] = set()
    
    for key in self.context.keys():
      git_match = re.match(r'revision_(\d+)_git', key)
      svn_match = re.match(r'revision_(\d+)_svn', key)
      
      if git_match:
        git_revisions.add(int(git_match.group(1)))
      if svn_match:
        svn_revisions.add(int(svn_match.group(1)))
    
    all_revisions = sorted(git_revisions.union(svn_revisions))
    
    if not all_revisions:
      self.context['revision_summary'] = ''
      return
    
    template_path = os.path.join('sections', 'revision.j2')
    revision_template = self.env.get_template(template_path)
    
    summaries: List[str] = []
    for rev_num in all_revisions:
      render_data: Dict[str, object] = {
        'revision_num': str(rev_num),
        'data': self.context,
        'has_conflicts_git': f'revision_{rev_num}_conflict_git' in self.context.keys(),
        'has_conflicts_svn': f'revision_{rev_num}_conflict_svn' in self.context.keys(),
      }
      summaries.append(revision_template.render(render_data))
    
    self.context['revision_summary'] = '\n'.join(summaries)

  def _render_template(self, template_name: str) -> str:
    if self.env.loader is None:
      raise RuntimeError("Jinja loader not initialized. Provide self.report_dir.")
    template_source, _, _ = self.env.loader.get_source(self.env, template_name)
    ast = self.env.parse(template_source)
    required_vars = meta.find_undeclared_variables(ast)

    render_kwargs = {v: self.context.get(v, "") for v in required_vars}
    
    template = self.env.get_template(template_name)
    return template.render(**render_kwargs)