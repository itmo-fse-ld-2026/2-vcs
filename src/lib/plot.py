from typing import Dict, List, Protocol
import json
import subprocess

class Plotter(Protocol):
  def generate_block_schema(self, raw_branches: str) -> str:
    ...
  
  def generate_pdf_graph(self, dot_content: str) -> bytes:
    ...

class DefaultPlotter:
  def __init__(self, colors: Dict[int, str],
                     scale_by_x: float,
                     offset_by_x: float,
                     scale_by_y: float,
                     offset_by_y: float) -> None:
    self.colors = colors
    self.scale_by_x = scale_by_x
    self.scale_by_y = -scale_by_y
    self.offset_by_x = offset_by_x
    self.offset_by_y = -offset_by_y

  def generate_block_schema(self, raw_branches: str) -> str:
    tikz_lines: List[str] = [
      "\\begin{tikzpicture}",
      "  [every node/.style={font=\\scriptsize}]"
    ]
    branches = json.loads(raw_branches)
    for branch in branches.values():
      color: str = self.colors.get(branch["user"], "black")
      b_id: int = branch["id"]
      
      if branch.get("parent") is not None and branch.get("merge") is not None:
        p_commit: int = branch["parent"]["commit"]
        p_branch_id: int = branches[branch["parent"]["branch"]]["id"]
        m_commit: int = branch["merge"]["commit"]
        m_branch_id: int = branches[branch["merge"]["branch"]]["id"]

        y_target: float = b_id * self.scale_by_y + self.offset_by_y
        y_p: float = p_branch_id * self.scale_by_y + self.offset_by_y
        y_m: float = m_branch_id * self.scale_by_y + self.offset_by_y
        x_p: float = p_commit * self.scale_by_x + self.offset_by_x
        x_m: float = m_commit * self.scale_by_x + self.offset_by_x

        tikz_lines.append(f"  \\draw[{color}] ({x_p}, {y_p}) -- ({x_p}, {y_target});")
        tikz_lines.append(f"  \\draw[{color}] ({x_m}, {y_m}) -- ({x_m}, {y_target});")
        tikz_lines.append(f"  \\draw[{color}] ({x_p}, {y_target}) -- ({x_m}, {y_target});")
      else:
        x_start: float = branch["commits"][0] * self.scale_by_x + self.offset_by_x
        x_end: float = branch["commits"][-1] * self.scale_by_x + self.offset_by_x
        y_pos: float = b_id * self.scale_by_y + self.offset_by_y
        tikz_lines.append(f"  \\draw[{color}] ({x_start}, {y_pos}) -- ({x_end}, {y_pos});")

    for branch in branches.values():
      color: str = self.colors.get(branch["user"], "black")
      b_id: int = branch["id"]
      for commit in branch["commits"]:
        x_pos: float = commit * self.scale_by_x + self.offset_by_x
        y_pos: float = b_id * self.scale_by_y + self.offset_by_y
        tikz_lines.append(f"  \\fill[{color}] ({x_pos}, {y_pos}) circle (2pt);")
        tikz_lines.append(f"  \\node[above] at ({x_pos}, {y_pos}) {{r{commit}}};")

    tikz_lines.append("\\end{tikzpicture}")
    return "\n".join(tikz_lines)

  def generate_pdf_graph(self, dot_content: str) -> bytes:
    try:
      result = subprocess.run(
        ["dot", "-Tpdf"],
        input=dot_content.encode('utf-8'),
        capture_output=True,
        check=True
      )
      return result.stdout
    except subprocess.CalledProcessError as e:
      raise RuntimeError(f"Graphviz failed: {e.stderr}")
    except FileNotFoundError:
      raise RuntimeError("Graphviz 'dot' executable not found in PATH.")