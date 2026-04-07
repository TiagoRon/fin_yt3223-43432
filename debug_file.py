import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)

# Redirect all stdout and stderr to a file
log_file = open("test_crash.log", "w", encoding="utf-8")
sys.stdout = log_file
sys.stderr = log_file

from src.config_manager import ConfigManager
from main import run_batch

config = ConfigManager()
google_key = config.get_api_key("google_gemini")
pexels_key = config.get_api_key("pexels")
if google_key: os.environ["GOOGLE_API_KEY"] = google_key
if pexels_key: os.environ["PEXELS_API_KEY"] = pexels_key

print("=" * 50)
print("  DEBUGGING RUN_BATCH TO LOG FILE")
print("=" * 50)

def custom_log(msg):
    print(f"[LOG] {msg}", flush=True)

def progress_cb(pct, title="", status="", sub_status=""):
    print(f"[PROG] {int(pct*100)}% {status} {sub_status}", flush=True)

try:
    result = run_batch(
        count=1,
        topic=None,
        use_trends=False,
        style="curiosity",
        log_func=custom_log,
        watermark_text="@Debug",
        lang="es",
        is_test=True,
        progress_callback=progress_cb,
        is_cancelled=None,
        loc=None
    )
    print("\n--- RUN BATCH FINISHED ---", flush=True)
    print(f"Result: {result}", flush=True)
except Exception as e:
    print("\n--- CRITICAL EXCEPTION IN SCRIPT ---", flush=True)
    import traceback
    traceback.print_exc()

log_file.close()
