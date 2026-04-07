import sys
import os
import requests
from dotenv import load_dotenv

load_dotenv()
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")

headers = {"Authorization": PEXELS_API_KEY}
url = "https://api.pexels.com/videos/search"
queries = ["Albert Einstein", "Cleopatra", "Julius Caesar"]

for q in queries:
    params = {"query": q, "per_page": 15}
    response = requests.get(url, headers=headers, params=params)
    videos = response.json().get('videos', [])
    valid_videos = []
    for v in videos:
        v_url = v.get('url', '').lower()
        # Check if any part of the query is in the url to be slightly lenient
        # Or require the full name
        name_dashed = q.lower().replace(" ", "-")
        if name_dashed in v_url:
            valid_videos.append(v)
            
    if valid_videos:
        print(f"Query: '{q}' -> Found {len(valid_videos)} REAL videos. First URL: {valid_videos[0]['url']}")
    else:
        print(f"Query: '{q}' -> 0 real videos (All fuzzy garbage)")
