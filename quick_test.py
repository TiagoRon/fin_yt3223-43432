"""Quick test script to generate a test video with new effects."""
import os
import sys
import codecs

# Force UTF-8
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

# Setup
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
print("  QUICK TEST - New Effects & Transitions")
print("=" * 50)

def progress(pct, status_text="", sub_text="", **kwargs):
    bar = "█" * int(pct * 30) + "░" * (30 - int(pct * 30))
    print(f"\r  [{bar}] {int(pct*100)}% {status_text} {sub_text}", end="", flush=True)
    if pct >= 1.0:
        print()

result = run_batch(
    count=1,
    topic=None,
    use_trends=False,
    style="curiosity",
    log_func=print,
    watermark_text="@TestEffects",
    lang="es",
    is_test=True,
    progress_callback=progress,
    is_cancelled=None,
    loc=None
)

if result:
    print(f"\n✅ Test video generated successfully!")
    print(f"   Output folder: {result[0] if result else 'N/A'}")
else:
    print(f"\n❌ Test video generation failed.")
