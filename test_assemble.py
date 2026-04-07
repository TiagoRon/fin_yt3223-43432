import moviepy.editor as mp
import time
import sys
import traceback
from PIL import Image

if not hasattr(Image, 'ANTIALIAS'):
    Image.ANTIALIAS = Image.LANCZOS

print("Starting test...")

try:
    # 1. Create a dummy video clip (2 seconds, red)
    base_clip = mp.ColorClip(size=(1080, 1920), color=(255, 0, 0), duration=2)
    
    # 2. Try the 'punch zoom' resize logic
    zoom_factor = 1.15
    
    # Static resize (FAST) vs Dynamic resize (SLOW)
    print("Testing static resize...")
    start_time = time.time()
    
    # This is what might be freezing the PC / or crashing
    c = base_clip.resize(zoom_factor)
    c = c.crop(x_center=c.w/2, y_center=c.h/2, width=1080, height=1920)
    
    # Write to file
    print("Writing to file...")
    c.write_videofile("test_output.mp4", fps=24, preset="ultrafast", audio=False)
    
    print(f"Success! Time taken: {time.time() - start_time:.2f}s")

except Exception as e:
    print(f"CRASH OCCURRED: {e}")
    traceback.print_exc()
