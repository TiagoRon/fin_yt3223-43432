import subprocess

log = subprocess.check_output(['git', 'log', '-p', 'src/video_editor.py']).decode('utf-8', errors='ignore')

# find lines matching `resize(lambda` inside `create_karaoke_clips`
lines = log.split('\n')
in_karaoke = False

for i, line in enumerate(lines):
    if "def create_karaoke_clips" in line:
        in_karaoke = True
    elif in_karaoke and line.startswith("def "):
        in_karaoke = False
        
    if in_karaoke and "resize(lambda" in line:
        print(f"Match context:")
        for j in range(max(0, i-5), min(len(lines), i+6)):
            print(lines[j])
        print("-" * 40)
