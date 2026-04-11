import requests
import re
import os
import subprocess

class IFMOPortalClient:
  def __init__(self, variant: int, base_url: str) -> None:
    self._base_url = base_url
    self._session = requests.Session()
    self._p_auth = self._get_auth_token()
    self._variant = variant

  def _get_auth_token(self) -> str:
    response = self._session.get(self._base_url)
    response.raise_for_status()
    match = re.search(r'p_auth=([^&"\']+)', response.text)
    if not match:
      raise ValueError("Could not find 'p_auth' token in the page source.")
    return match.group(1)

  def _build_params(self, extra_params: dict[str, str]) -> dict[str, str]:
    params = {
      "p_p_id": "selab2_WAR_seportlet",
      "p_p_state": "normal",
      "p_p_mode": "view",
      "p_auth": self._p_auth
    }
    params.update(extra_params)
    return params

  def _post(self, extra_params: dict[str, str], payload: dict[str, str], stream: bool = False) -> requests.Response:
    return self._session.post(
      self._base_url,
      params=self._build_params(extra_params),
      data=payload,
      stream=stream
    )

  def download_archive(self, commit: int):
    params = {
      "p_p_lifecycle": "2",
      "p_p_cacheability": "cacheLevelPage"
    }
    payload = {
      "variant": str(self._variant),
      "commit": str(commit)
    }
    response = self._post(params, payload, stream=True)
    
    if response.ok:
      filename = f"{commit}.zip"
      with open(filename, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
          f.write(chunk)
      return True, filename, response.status_code
    return False, response.text[:500], response.status_code

  def get_branches(self):
    params = {
      "p_p_lifecycle": "1",
      "_selab2_WAR_seportlet_javax.portlet.action": "getBranches"
    }
    payload = {
      "variant": str(self._variant)
    }
    response = self._post(params, payload)
    
    if response.ok:
      return True, response.text, response.status_code
    return False, response.text[:500], response.status_code
  
  def get_commit_area(self, commit: int, base_path: str) -> str:
    target_dir = os.path.join(base_path, str(commit))
    if os.path.exists(target_dir):
      return target_dir

    success, file_path, _ = self.download_archive(commit)
    if not success:
      raise RuntimeError(f"Failed to download commit {commit}")

    os.makedirs(target_dir, exist_ok=True)
    result = subprocess.run(
      ["unzip", "-q", file_path, "-d", target_dir],
      capture_output=True,
      text=True
    )

    if result.returncode != 0:
      if not os.path.exists(target_dir) or not os.listdir(target_dir):
        raise RuntimeError(f"Unzip failed: {result.stderr}")
    
    os.remove(file_path)
    return target_dir

  def get_diff(self, old_dir: str, new_dir: str) -> str:
    result = subprocess.run(
      ["diff", "-r", "-N", "--color=always", "--binary", old_dir, new_dir],
      capture_output=True,
      text=True,
      errors="replace"
    )
    if result.returncode > 1:
      raise RuntimeError(f"Diff command failed: {result.stderr}")
    return result.stdout