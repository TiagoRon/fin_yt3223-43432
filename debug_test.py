"""Debugging script to find out exactly what assemble_video and run_batch are doing."""
import os
import sys
import codecs

# Force UTF-8
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)

from src.config_manager import ConfigManager
from main import run_batch

config = ConfigManager()

# Load API keys from config
google_key = config.get_api_key("google_gemini")
pexels_key = config.get_api_key("pexels")

if google_key:
    os.environ["GOOGLE_API_KEY"] = google_key
if pexels_key:
    os.environ["PEXELS_API_KEY"] = pexels_key

print("=" * 50)
print("  DEBUGGING RUN_BATCH")
print("=" * 50)

def custom_log(msg):
    # Print on a newline so we don't overwrite the progress bar
    print("\n[LOG] " + msg)

def progress_cb(pct, title="", status="", sub_status=""):
    bar = "█" * int(pct * 30) + "░" * (30 - int(pct * 30))
    # We use a \r print here but log_func will print \n so it's clean
    print(f"\r  [{bar}] {int(pct*100)}% {status} {sub_status}", end="", flush=True)

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
    print("\n\n--- RUN BATCH FINISHED ---")
    print(f"Result type: {type(result)}")
    print(f"Result value: {result}")
except Exception as e:
    print("\n\n--- CRITICAL EXCEPTION IN SCRIPT ---")
    import traceback
    traceback.print_exc()

