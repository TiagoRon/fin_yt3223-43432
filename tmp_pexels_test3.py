import sys
import os
import requests
from dotenv import load_dotenv

load_dotenv()
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")
if not PEXELS_API_KEY:
    print("No API key")
    sys.exit(1)

headers = {"Authorization": PEXELS_API_KEY}
url = "https://api.pexels.com/videos/search"
queries = ["Albert Einstein", "Cleopatra"]

for q in queries:
    params = {
        "query": q,
        "per_page": 1,
        "orientation": "portrait"
    }
    response = requests.get(url, headers=headers, params=params)
    data = response.json()
    videos = data.get('videos', [])
    if videos:
        print(f"Query: '{q}' -> Found Video ID: {videos[0]['id']} -> User: {videos[0].get('user', {}).get('name')}")
    else:
        print(f"Query: '{q}' -> No videos")
