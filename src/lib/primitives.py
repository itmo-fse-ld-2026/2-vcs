from typing import List, Optional
from dataclasses import dataclass

@dataclass
class Commit:
  id: int
  message: str

@dataclass
class Link:
  branch: int
  commit: int

@dataclass
class Branch:
  name: str
  id: int
  user: int
  commits: List[int]
  parent: Optional[Link] = None
  merge: Optional[Link] = None

@dataclass
class User:
  name: str
  email: str
  id: int
  branch: int