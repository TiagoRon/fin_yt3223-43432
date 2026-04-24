import os
import json
import time
from datetime import datetime
from src.upload_utils import extract_archive

def process_archives_recursively(directory, depth=0):
    """
    Recursively finds and extracts .rar and .zip files within a directory tree.
    To prevent infinite loops, it limits depth and renames processed files.
    """
    if depth > 5: # Safety limit
        return False
        
    extracted_any = False
    
    # We use a list to store what we found to avoid modifying the tree while walking
    to_extract = []
    
    for root, dirs, files in os.walk(directory):
        for f in files:
            f_lower = f.lower()
            if (f_lower.endswith(".rar") or f_lower.endswith(".zip")) and not f_lower.endswith(".extraido"):
                to_extract.append(os.path.join(root, f))
                
    for f_path in to_extract:
        f_dir = os.path.dirname(f_path)
        f_name = os.path.basename(f_path)
        timestamp = int(time.time())
        # Create a unique folder for extraction
        folder_name = f"auto_extracted_{os.path.splitext(f_name)[0]}_{timestamp}"
        target_dir = os.path.join(f_dir, folder_name)
        
        print(f">>> [RECURSIVE] Decompressing: {f_name} at depth {depth}")
        if extract_archive(f_path, target_dir):
            extracted_any = True
            # Mark original as processed
            try:
                os.rename(f_path, f_path + ".extraido")
            except:
                pass
                
    # If we extracted something, there might be more archives inside!
    if extracted_any:
        process_archives_recursively(directory, depth + 1)
        return True
    
    return False

def get_video_history(output_dir):
    """
    Scans the output directory for generated videos and returns a list of metadata.
    Each subfolder in output_dir is expected to contain a video file and metadata.
    """
    history = []
    if not os.path.exists(output_dir):
        return []

    # --- RECURSIVE AUTO-EXTRACTION ---
    process_archives_recursively(output_dir)

    # Walk through the output directory
    for root, dirs, files in os.walk(output_dir):
        video_file = None
        metadata_file = None
        
        # Look for video files
        mp4_files = [f for f in files if f.endswith(".mp4")]
        if mp4_files:
            # Prioritize files that don't have 'part' or 'scene' in name
            main_videos = [f for f in mp4_files if "part" not in f.lower() and "scene" not in f.lower()]
            video_file_name = main_videos[0] if main_videos else mp4_files[0]
            video_file = os.path.join(root, video_file_name)
            
            # --- PROACTIVE RENAMING OF 'short_final.mp4' ---
            # If we find the generic name, try to rename it to something better based on the folder
            if video_file_name.lower() == "short_final.mp4":
                try:
                    folder_name = os.path.basename(root)
                    # Create a safe name from folder
                    import re
                    safe_name = re.sub(r'[^a-zA-Z0-9]', '_', folder_name)
                    if not safe_name: safe_name = "video"
                    new_path = os.path.join(root, f"{safe_name}.mp4")
                    
                    # Only rename if the target doesn't exist
                    if not os.path.exists(new_path):
                        os.rename(video_file, new_path)
                        video_file = new_path
                        print(f"🔄 Fixed generic filename: {video_file_name} -> {os.path.basename(new_path)}")
                except Exception as e_rename:
                    print(f"⚠️ Could not rename generic file: {e_rename}")
        
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
