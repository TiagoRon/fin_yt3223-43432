import os
import json
from datetime import datetime

def get_video_history(output_dir):
    """
    Scans the output directory for generated videos and returns a list of metadata.
    Each subfolder in output_dir is expected to contain a video file and metadata.
    """
    history = []
    if not os.path.exists(output_dir):
        return []

    # Walk through the output directory
    for root, dirs, files in os.walk(output_dir):
        video_file = None
        metadata_file = None
        
        # Look for video files
        # Better detection: Look for 'short_final.mp4' which is our actual output
        short_final = next((f for f in files if f.lower() == "short_final.mp4"), None)
        if short_final:
            video_file = os.path.join(root, short_final)
        else:
            # Fallback to any mp4, but skip scene parts if possible
            mp4_files = [f for f in files if f.endswith(".mp4")]
            if mp4_files:
                # Prioritize files that don't have 'part' or 'scene' in name if available
                main_videos = [f for f in mp4_files if "part" not in f.lower() and "scene" not in f.lower()]
                if main_videos:
                    video_file = os.path.join(root, main_videos[0])
                else:
                    video_file = os.path.join(root, mp4_files[0])
        
        json_path = os.path.join(root, "metadata.json")
        txt_path = os.path.join(root, "metadata.txt")
        
        # We consider this folder valid if it has a video OR it has metadata (which may be a deleted video)
        if video_file or os.path.exists(json_path) or os.path.exists(txt_path):
            video_path_record = video_file if video_file else root
            
            # Look for metadata (metadata.json or metadata.txt)
            metadata = {
                "title": os.path.basename(root),
                "date": "N/A",
                "path": video_path_record,
                "status": "generated"
            }
            
            # Check for metadata.json first
            json_path = os.path.join(root, "metadata.json")
            if os.path.exists(json_path):
                try:
                    with open(json_path, 'r', encoding='utf-8') as jf:
                        data = json.load(jf)
                        metadata["title"] = data.get("title", metadata["title"])
                        if "style" in data:
                            metadata["style"] = data.get("style")
                        if "mood" in data:
                            metadata["mood"] = data.get("mood")
                        
                        # Apply saved status if available (e.g. uploaded or cancelled)
                        if data.get("status"):
                            metadata["status"] = data.get("status")
                        elif data.get("uploaded"):
                            metadata["status"] = "uploaded"
                except:
                    pass
            
            # Check for metadata.txt
            txt_path = os.path.join(root, "metadata.txt")
            if os.path.exists(txt_path):
                # We could parse this too, but JSON is preferred
                pass
                
            # Use folder modification time as date
            try:
                mtime = os.path.getmtime(root)
                metadata["date"] = datetime.fromtimestamp(mtime).strftime("%d/%m/%Y %H:%M")
            except:
                pass
                
            history.append(metadata)

    # Sort history by date descending
    def parse_date(date_str):
        if date_str == "N/A":
            return datetime.min
        try:
            return datetime.strptime(date_str, "%d/%m/%Y %H:%M")
        except:
            return datetime.min
            
    try:
        history.sort(key=lambda x: parse_date(x.get("date", "N/A")), reverse=True)
    except Exception as e:
        print(f"Error sorting history: {e}")
        
    return history
