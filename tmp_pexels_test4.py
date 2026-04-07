import sys
import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")

headers = {"Authorization": PEXELS_API_KEY}
url = "https://api.pexels.com/videos/videos/4064867"
response = requests.get(url, headers=headers)
print(json.dumps(response.json(), indent=2))
