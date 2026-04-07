import os
import sys

# Ensure local imports work correctly
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.ai_client import generate_script
import json

if __name__ == "__main__":
    print("Testing generate_script...")
    data = generate_script(topic="las 3 batallas mas epicas de dragon ball z", style="top_3", lang="es")
    
    print("\n\n=== RESPONSE ===")
    print(json.dumps(data, indent=2, ensure_ascii=False))
