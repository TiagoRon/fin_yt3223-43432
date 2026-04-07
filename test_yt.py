import os
import sys

# Add current path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.stock_client import get_youtube_clip

def main():
    print("Testing YT-DLP")
    success = get_youtube_clip("Guillermo Francella El Clan scene", "test_yt_output.mp4")
    print(f"Success: {success}")

if __name__ == "__main__":
    main()
