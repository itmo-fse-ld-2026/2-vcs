from lib.client import IFMOPortalClient

if __name__ == "__main__":
  client = IFMOPortalClient()

  success, result, status = client.get_branches(variant=2)
  if success:
    print(f"Success! Status Code: {status}\n{result}")
  else:
    print(f"Something went wrong!\nStatus Code: {status}\nError Response: {result}")

  success, result, status = client.download_archive(variant=213, commit=4)
  if success:
    print(f"Success! File saved as '{result}'. Status Code: {status}")
  else:
    print(f"Something went wrong!\nStatus Code: {status}\nError Response: {result}")