import os
import threading
import time
from datetime import datetime, date, timedelta
from src.uploader import get_driver, upload_video_selenium, open_browser_for_login, check_login_status, logout_user
from src.upload_utils import extract_archive, parse_metadata

class UploadManager:
    def __init__(self, log_callback=print, progress_callback=None, loc=None):
        self.log = log_callback
        self.progress_callback = progress_callback  # (current, total, video_name, status)
        self.loc = loc
        self.driver = None
        self.stop_flag = False
        
    def is_logged_in(self):
        """Checks if the user is already logged in securely."""
        return check_login_status()
        
    def logout(self):
        """Logs the user out by deleting their stored profile."""
        return logout_user()
        
    def open_login_window(self, on_success=None):
        """
        Runs the login browser in a separate thread to not block GUI.
        """
        def _run():
            self.log("Opening Login Window...")
            open_browser_for_login(on_login_success=on_success)
            self.log("Login Window Closed.")
            
        t = threading.Thread(target=_run)
        t.daemon = True
        t.start()
        
    def start_process(self, video_list, mode="schedule", start_date=None, start_hour=None, interval_hours=None):
        """
        Starts the upload process in a separate thread.
        video_list: list of dicts [{"path": "...", "meta": {...}}, ...]
        mode: 'schedule' (slots) or 'now' (immediate public)
        """
        self.stop_flag = False
        t = threading.Thread(target=self._process_loop, args=(video_list, mode, start_date, start_hour, interval_hours))
        t.start()
        
    def stop(self):
        self.stop_flag = True
        try:
            if self.driver:
                self.driver.quit()
        except:
            pass

    def start_process_mixed(self, items, progress_callback=None):
        """
        Uploads a list of items, each with its own mode (_mode='now' or 'schedule').
        Uses a SINGLE browser session for all videos.
        """
        if progress_callback:
            self.progress_callback = progress_callback
        self.stop_flag = False
        t = threading.Thread(target=self._process_mixed_loop, args=(items,))
        t.start()

    def _process_mixed_loop(self, items):
        if not items:
            self.log("No videos provided for upload.")
            return

        total = len(items)
        try:
            self.log("Initializing Browser for Upload...")
            if self.progress_callback:
                self.progress_callback(0, total, "", "initializing")
            self.driver = get_driver(headless=True)
            time.sleep(5) # Stability delay: wait for browser to fully initialize session
        except Exception as e:
            error_msg = str(e)
            if "session not created" in error_msg.lower() or "user data directory is already in use" in error_msg.lower():
                error_msg = "PERFIL BLOQUEADO: Cierra todas las ventanas de Chrome y reintenta."
            
            self.log(f"Failed to start browser: {error_msg}")
            if self.progress_callback:
                self.progress_callback(0, total, error_msg, "error")
            return
        try:
            success_count = 0
            fail_count = 0
            self.log(f"Starting Upload Process ({total} videos)")
            if self.progress_callback:
                self.progress_callback(0, total, "", "starting")

            for i, item in enumerate(items):
                if self.stop_flag:
                    break

                video_path = item.get("path")
                meta = item.get("meta", {})
                item_mode = item.get("_mode", "now")

                if not video_path or not os.path.exists(video_path):
                    self.log(f"Skipping missing file: {video_path}")
                    continue

                vname = os.path.basename(video_path)
                self.log(f"[{i+1}/{total}] Uploading: {vname}")
                if self.progress_callback:
                    self.progress_callback(i, total, vname, "uploading")

                # Check if driver is still alive, recreate if needed
                try:
                    _ = self.driver.title
                except:
                    self.log("Browser session lost, restarting...")
                    try:
                        self.driver.quit()
                    except: pass
                    self.driver = get_driver(headless=True)
                    time.sleep(2)

                if item_mode == "schedule":
                    sd = item.get("_schedule_date")
                    sh = item.get("_schedule_hour", 12)
                    sch_date = sd.strftime("%d/%m/%Y") if sd else None
                    sch_time = f"{sh:02d}:00"
                    self.log(f" -> Scheduled: {sch_date} {sch_time}")
                    privacy = "schedule"
                else:
                    sch_date = None
                    sch_time = None
                    self.log(" -> Immediate Upload (Public)")
                    privacy = "public"

                success = upload_video_selenium(
                    self.driver,
                    video_path,
                    meta.get("title", os.path.basename(video_path)),
                    meta.get("description", ""),
                    meta.get("tags", []),
                    privacy_status=privacy,
                    schedule_date=sch_date,
                    schedule_time=sch_time,
                    cancel_check=lambda: self.stop_flag
                )

                if success == "not_logged_in":
                    self.log("❌ CRITICAL: No session found. Aborting process.")
                    if self.progress_callback:
                        self.progress_callback(i, total, "Debes hacer LOGIN primero", "error")
                    break

                if success:
                    success_count += 1
                    self.log(f"✅ [{i+1}/{total}] Upload Successful")
                    if self.progress_callback:
                        self.progress_callback(i + 1, total, vname, "done")
                    try:
                        import json
                        meta_path = os.path.join(os.path.dirname(video_path), "metadata.json")
                        if os.path.exists(meta_path):
                            with open(meta_path, 'r', encoding='utf-8') as f:
                                jdata = json.load(f)
                            jdata["uploaded"] = True
                            jdata["status"] = "uploaded"
                            with open(meta_path, 'w', encoding='utf-8') as f:
                                json.dump(jdata, f, indent=4, ensure_ascii=False)
                    except Exception as meta_e:
                        self.log(f"Failed to save upload status: {meta_e}")
                else:
                    fail_count += 1
                    self.log(f"❌ [{i+1}/{total}] Upload Failed")
                    if self.progress_callback:
                        self.progress_callback(i + 1, total, vname, "failed")

                time.sleep(1)

            summary_msg = f"Done: {success_count} success, {fail_count} failed."
            self.log(f"All tasks completed. {summary_msg}")
            if self.progress_callback:
                self.progress_callback(total, total, summary_msg, "completed")

        except Exception as e:
            self.log(f"Process Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.log("Session ended. Closing browser...")
            time.sleep(2)
            try:
                if self.driver:
                    self.driver.quit()
            except:
                pass
        
    def _process_loop(self, video_list, mode, start_date, start_hour, interval_hours):
        if not video_list:
            self.log("No videos provided for upload.")
            return

        # 1. Initialize Driver
        try:
            self.log("Initializing Browser for Upload...")
            self.driver = get_driver(headless=True)
            time.sleep(5) # Stability delay
        except Exception as e:
            self.log(f"Failed to start browser: {e}")
            return

        try:
            total = len(video_list)
            self.log(f"Starting Upload Process ({total} videos, Mode: {mode.upper()})")
            if self.progress_callback:
                self.progress_callback(0, total, "", "starting")

            if mode == "schedule":
                current_date = start_date if start_date else datetime.now().date()
                current_hour = start_hour if start_hour is not None else 12
                interval = interval_hours if interval_hours is not None else 2
                self.log(f"Scheduling starts at: {current_date} {current_hour}:00 with interval {interval}h")

            # 3. Process Files
            for i, item in enumerate(video_list):
                if self.stop_flag: break
                
                video_path = item.get("path")
                meta = item.get("meta", {})
                
                if not video_path or not os.path.exists(video_path):
                    self.log(f"Skipping missing file: {video_path}")
                    continue
                
                vname = os.path.basename(video_path)
                self.log(f"[{i+1}/{total}] Uploading: {vname}")
                if self.progress_callback:
                    self.progress_callback(i, total, vname, "uploading")
                
                if mode == "schedule":
                    sch_time = f"{current_hour:02d}:00"
                    sch_date = current_date.strftime("%d/%m/%Y")
                    self.log(f" -> Scheduled: {sch_date} {sch_time}")
                    privacy = "schedule"
                else:
                    sch_time = None
                    sch_date = None
                    self.log(" -> Immediate Upload (Public)")
                    privacy = "public"
                
                success = upload_video_selenium(
                    self.driver,
                    video_path,
                    meta.get("title", vname),
                    meta.get("description", ""),
                    meta.get("tags", []),
                    privacy_status=privacy,
                    schedule_date=sch_date,
                    schedule_time=sch_time,
                    cancel_check=lambda: self.stop_flag
                )
                
                if self.stop_flag: break
                
                if success:
                    self.log(f"✅ [{i+1}/{total}] Upload Successful")
                    if self.progress_callback:
                        self.progress_callback(i + 1, total, vname, "done")
                    try:
                        import json
                        meta_path = os.path.join(os.path.dirname(video_path), "metadata.json")
                        if os.path.exists(meta_path):
                            with open(meta_path, 'r', encoding='utf-8') as f:
                                jdata = json.load(f)
                            jdata["uploaded"] = True
                            jdata["status"] = "uploaded"
                            with open(meta_path, 'w', encoding='utf-8') as f:
                                json.dump(jdata, f, indent=4, ensure_ascii=False)
                    except Exception as meta_e:
                        self.log(f"Failed to save upload status: {meta_e}")
                else:
                    self.log(f"❌ [{i+1}/{total}] Upload Failed")
                    if self.progress_callback:
                        self.progress_callback(i + 1, total, vname, "failed")
                    
                if mode == "schedule":
                    # Advance Schedule
                    if interval > 0:
                        current_hour += interval
                        while current_hour >= 24:
                            current_hour -= 24
                            current_date += timedelta(days=1)
            
            if not self.stop_flag:
                self.log("All tasks completed.")
                if self.progress_callback:
                    self.progress_callback(total, total, "", "completed")
            else:
                self.log("Upload tasks cancelled.")
            
        except Exception as e:
            self.log(f"Process Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # Keep driver open?
            self.log("Session ended. Closing browser in 5s...")
            time.sleep(5)
            try:
               if self.driver: self.driver.quit()
            except: pass
