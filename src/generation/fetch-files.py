import requests
import re

COMMIT = 4
VARIANT = 213

session = requests.Session()

base_url = "https://se.ifmo.ru/courses/software-engineering-basics"
main_page = session.get(base_url)

auth_token_match = re.search(r'p_auth=([^&"\']+)', main_page.text)
if auth_token_match:
  p_auth = auth_token_match.group(1)
else:
  raise ValueError("Could not find 'p_auth' token in the page source.")

params = {
  "p_p_id": "selab2_WAR_seportlet",
  "p_p_lifecycle": "2",
  "p_p_state": "normal",
  "p_p_mode": "view",
  "p_p_cacheability": "cacheLevelPage",
  "p_auth": p_auth
}

payload = {
  "variant": str(VARIANT),
  "commit": str(COMMIT)
}

response = session.post(
  base_url,
  params=params,
  data=payload,
  stream=True
)

if response.ok:
  with open(f"{COMMIT}.zip", "wb") as f:
    for chunk in response.iter_content(chunk_size=8192):
      f.write(chunk)
  print(f"Success! File saved as 'downloaded_file'. Status Code: {response.status_code}")
else:
  print(f"Something went wrong!")
  print(f"Status Code: {response.status_code}")
  print(f"Error Response: {response.text[:500]}")