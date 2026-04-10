import requests, re

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
  "p_p_lifecycle": "1",
  "p_p_state": "normal",
  "p_p_mode": "view",
  "_selab2_WAR_seportlet_javax.portlet.action": "getBranches",
  "p_auth": p_auth
}

cookies = {
  "JSESSIONID": "VbL0xFtTmHKKA_xEevglLfv1O9xz8Cg3EcUbt6j8.lportal",
  "COOKIE_SUPPORT": "true",
  "GUEST_LANGUAGE_ID": "ru_RU"
}

payload = {
  "variant": "2"
}

response = session.post(
  base_url, 
  params=params, 
  cookies=cookies, 
  data=payload
)

if response.ok:
  print(f"Success! Status Code: {response.status_code}")
  print(response.text)
else:
  print(f"Something went wrong!")
  print(f"Status Code: {response.status_code}")
  print(f"Error Response: {response.text[:500]}")