import os
import patoolib
import shutil

def extract_rar(archive_path, output_dir):
    try:
        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)
        os.makedirs(output_dir)
        
        # patoolib handles rar/zip extraction automatically
        patoolib.extract_archive(archive_path, outdir=output_dir, verbosity=-1)
        return True
    except Exception as e:
        print(f"Extraction error: {e}")
        return False

def parse_metadata(txt_path):
    """
    Parses the text file to extract Title, Hashtags, and Script.
    Expected format:
    Title: ...
    Hashtags: ...
    Script: ...
    """
    if not os.path.exists(txt_path):
        return None
    
    metadata = {
        "title": "",
        "description": "",
        "tags": []
    }
    
    try:
        with open(txt_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        lines = content.split('\n')
        current_section = None
        script_lines = []
        
        for line in lines:
            line_lower = line.lower()
            if line_lower.startswith("title:"):
                metadata["title"] = line[6:].strip()
            elif line_lower.startswith("hashtags:"):
                # Clean up hashtags to be a list
                raw_tags = line[9:].strip().replace('#', '').split(' ')
                metadata["tags"] = [t for t in raw_tags if t]
                # Join them back for description if needed
                metadata["description"] += line + "\n\n"
            elif line_lower.startswith("script:"):
                current_section = "script"
                script_lines.append(line[7:].strip())
            elif current_section == "script":
                script_lines.append(line)
        
        metadata["description"] += "\n".join(script_lines)
        return metadata
    except Exception as e:
        print(f"Metadata parsing error: {e}")
        return None
