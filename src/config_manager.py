import json
import os

class ConfigManager:
    def __init__(self, filename="settings.json"):
        self.filename = filename
        self.data = self._load()

    def _load(self):
        if not os.path.exists(self.filename):
            return {
                "api_keys": {
                    "google_gemini": "",
                    "pexels": ""
                },
                "preferences": {
                    "language": "en",
                    "watermark": "@AIShortsGenerator"
                }
            }
        try:
            with open(self.filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}

    def save(self):
        with open(self.filename, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=4)

    def get_api_key(self, service):
        return self.data.get("api_keys", {}).get(service, "")

    def set_api_key(self, service, value):
        if "api_keys" not in self.data: self.data["api_keys"] = {}
        self.data["api_keys"][service] = value
        self.save()

    def get_preference(self, key, default=""):
        return self.data.get("preferences", {}).get(key, default)

    def set_preference(self, key, value):
        if "preferences" not in self.data: self.data["preferences"] = {}
        self.data["preferences"][key] = value
        self.save()
