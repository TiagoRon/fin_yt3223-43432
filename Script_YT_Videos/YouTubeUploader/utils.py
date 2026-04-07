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
    Combines Script and Hashtags into the Description.
    """
    metadata = {
        "title": "",
        "description": "",
        "tags": []
    }
    
    try:
        with open(txt_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        title = ""
        hashtags = ""
        script_lines = []
        
        for line in lines:
            stripped = line.strip()
            # Ignore empty lines at the very beginning if we haven't found anything yet? 
            # OR just keep them.
            
            lower_line = stripped.lower()
            
            if lower_line.startswith(("title:", "título:")):
                title = line.split(":", 1)[1].strip()
            elif lower_line.startswith(("hashtags:", "etiquetas:", "hashtag:")):
                hashtags = line.split(":", 1)[1].strip()
            else:
                # Assume this is part of the script/body
                # We keep the original formatting (newlines) of the script
                script_lines.append(line.rstrip()) 

        # Construct Description
        script_content = "\n".join(script_lines).strip()
        
        final_description = ""
        if hashtags:
            final_description += hashtags + "\n\n"
        
        final_description += script_content
        
        # Helper to extract clean tags from a hashtag string
        raw_tags = hashtags.replace("#", "")
        if "," in raw_tags:
            tag_list = [t.strip() for t in raw_tags.split(',') if t.strip()]
        else:
            tag_list = [t.strip() for t in raw_tags.split() if t.strip()]

        metadata["title"] = title if title else "Video sin título"
        metadata["description"] = final_description
        metadata["tags"] = tag_list
                     
    except Exception as e:
        print(f"Metadata parsing error: {e}")
        
    return metadata
