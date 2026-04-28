import os
import requests
import zipfile
import io
import time
from src.upload_utils import extract_archive

class GitHubSync:
    def __init__(self, token, repo, log_callback=print):
        self.token = token.strip() if token else ""
        self.repo = repo.strip() if repo else ""
        self.log = log_callback
        self.base_url = f"https://api.github.com/repos/{self.repo}"
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }

    def sync_latest(self, output_dir, last_id=None, force=False):
        """
        Fetches the latest 'daily_videos' artifact and extracts it to output_dir.
        """
        if not self.token or not self.repo:
            self.log("GitHub Token or Repo not configured.")
            return False

        try:
            self.log(f"Fetching artifacts for {self.repo}...")
            response = requests.get(f"{self.base_url}/actions/artifacts", headers=self.headers)
            
            if response.status_code == 401:
                self.log("Error: GitHub Token is invalid (Bad credentials). Please check your PAT in Settings.")
                return False, None, None
            elif response.status_code != 200:
                self.log(f"Error fetching artifacts: {response.status_code} - {response.text}")
                return False, None, None
                
            data = response.json()
            artifacts = data.get("artifacts", [])
            
            # Filter for 'DAILY_VIDEOS' (More flexible: check if it's IN the name)
            daily_artifacts = [a for a in artifacts if "DAILY_VIDEOS" in a["name"].upper()]
            
            if not daily_artifacts:
                self.log("No artifacts named 'daily_videos' found.")
                return False, None, None
                
            # Take the most recent one
            latest = daily_artifacts[0]
            artifact_id = str(latest["id"])
            created_at_str = latest["created_at"]
            
            # 1. Date Check: Only download if it's from TODAY (using UTC to match GitHub)
            from datetime import datetime, timezone
            current_date_utc = datetime.now(timezone.utc).date()
            artifact_date = datetime.strptime(created_at_str[:10], "%Y-%m-%d").date()
            
            is_today = (artifact_date == current_date_utc)
            if not is_today:
                self.log(f"Latest artifact is from {artifact_date}, not today ({current_date_utc}). Skipping.")
                return "already_old", None, None

            # 2. Duplicate & Missing Check
            is_duplicate = (not force and last_id and str(artifact_id) == str(last_id))
            
            if is_duplicate:
                # If it's a duplicate ID, check if the files actually exist in output_dir
                # We look for any folder starting with 'github_videos_' that isn't empty
                has_files = False
                for d in os.listdir(output_dir):
                    if d.startswith("github_videos_"):
                        full_d = os.path.join(output_dir, d)
                        if os.path.isdir(full_d):
                            # Check if there's any mp4 inside (recursive-ish)
                            for root, _, files in os.walk(full_d):
                                if any(f.lower().endswith(".mp4") for f in files):
                                    has_files = True
                                    break
                    if has_files: break
                
                if has_files:
                    self.log(f"Artifact {artifact_id} was already synced and files exist. Skipping.")
                    return "already_synced", None, None
                else:
                    self.log(f"Artifact {artifact_id} was synced before but files are missing. Re-downloading...")
            
            self.log(f"Found latest artifact ID: {artifact_id} (Created at {created_at_str})")
            
            # Download zip
            download_url = latest["archive_download_url"]
            self.log("Downloading artifact zip...")
            
            dl_resp = requests.get(download_url, headers=self.headers, stream=True)
            if dl_resp.status_code != 200:
                self.log(f"Download failed: {dl_resp.status_code}")
                return False
                
            # Use a temporary name so the automatic scanner ignores it while downloading
            timestamp = int(time.time())
            temp_zip_filename = f"github_sync_{timestamp}.syncing"
            zip_path = os.path.join(output_dir, temp_zip_filename)
            final_zip_path = os.path.join(output_dir, f"github_sync_{timestamp}.zip")
            
            with open(zip_path, 'wb') as f:
                for chunk in dl_resp.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # Now that it's fully downloaded, we can rename it or just use it
            self.log(f"Download complete. Extracting...")
            
            target_folder = f"github_videos_{timestamp}"
            target_path = os.path.join(output_dir, target_folder)
            
            if extract_archive(zip_path, target_path):
                self.log(f"Successfully synced videos to {target_folder}!")
                # Mark as extracted
                try:
                    os.rename(zip_path, final_zip_path + ".extraido")
                except:
                    # If rename fails, just remove the temp file
                    try: os.remove(zip_path)
                    except: pass
                return True, artifact_id, target_path
            else:
                self.log("Extraction failed.")
                return False, None, None
                
        except Exception as e:
            self.log(f"Sync logic error: {e}")
            return False, None, None
