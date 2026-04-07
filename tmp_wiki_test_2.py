import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from src.stock_client import get_wikipedia_image

print("Testing Einstein fetch:")
success = get_wikipedia_image("Albert Einstein", "test.jpg")
print(f"Result: {success}")
