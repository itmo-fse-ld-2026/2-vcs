import requests
import re

class IFMOPortalClient:
  def __init__(self, base_url: str = "https://se.ifmo.ru/courses/software-engineering-basics") -> None:
    self._base_url = base_url
    self._session = requests.Session()
    self._p_auth = self._get_auth_token()

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

  def download_archive(self, variant: int, commit: int):
    params = {
      "p_p_lifecycle": "2",
      "p_p_cacheability": "cacheLevelPage"
    }
    payload = {
      "variant": str(variant),
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

  def get_branches(self, variant: int):
    params = {
      "p_p_lifecycle": "1",
      "_selab2_WAR_seportlet_javax.portlet.action": "getBranches"
    }
    payload = {
      "variant": str(variant)
    }
    response = self._post(params, payload)
    
    if response.ok:
      return True, response.text, response.status_code
    return False, response.text[:500], response.status_code