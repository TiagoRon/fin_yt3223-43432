import sys
import os
import requests
import json

query = "Albert Einstein"
url = "https://en.wikipedia.org/w/api.php"
params = {
    "action": "query",
    "prop": "pageimages",
    "format": "json",
    "piprop": "original",
    "titles": query,
    "redirects": 1
}
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
}
try:
    response = requests.get(url, params=params, headers=headers, timeout=10)
    data = response.json()
    pages = data.get("query", {}).get("pages", {})
    for page_id, page_info in pages.items():
        if page_id == "-1": continue
        if "original" in page_info and "source" in page_info["original"]:
            img_url = page_info["original"]["source"]
            print(f"Downloading from: {img_url}")
            
            # Download
            img_resp = requests.get(img_url, timeout=15)
            # Wait, DOES THIS ALSO NEED HEADERS?
            img_resp_with_headers = requests.get(img_url, headers=headers, timeout=15)
            
            print(f"Without headers status: {img_resp.status_code}, length: {len(img_resp.content)}")
            print(f"With headers status: {img_resp_with_headers.status_code}, length: {len(img_resp_with_headers.content)}")
            
except Exception as e:
    print(f"Error: {e}")
