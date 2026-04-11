from typing import List, Optional
from dataclasses import dataclass

@dataclass
class Commit:
  id: int

@dataclass
class Link:
  branch: str
  commit: int

@dataclass
class Branch:
  name: str
  id: int
  user: int
  commits: List[int]
  parent: Optional[Link] = None
  merge: Optional[Link] = None