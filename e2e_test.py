import sys
import os

# Set current dir to LocalWithoutGithub
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import run_batch

if __name__ == "__main__":
    print("Running Quick Test...")
    run_batch(count=1, topic="Cleopatra", style="history", is_test=False)
