import os
import zipfile
import patoolib
import shutil

def extract_archive(archive_path, output_dir, is_recursive=False):
    """
    Extracts a compressed archive (RAR or ZIP) to the specified directory.
    Uses native zipfile for ZIP and patool for other formats.
    Supports nested archives recursively.
    """
    try:
        # Only clean the output_dir if it's the top-level call
        if not is_recursive:
            if os.path.exists(output_dir):
                shutil.rmtree(output_dir)
            os.makedirs(output_dir)
        elif not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        lower_path = archive_path.lower()
        extracted = False
        
        # Check if it's a ZIP (including our temporary names)
        if lower_path.endswith(".zip") or lower_path.endswith(".syncing") or ".zip.tmp_extract" in lower_path:
            print(f">>> [EXTRACT] Usando zipfile nativo para: {os.path.basename(archive_path)}")
            with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                zip_ref.extractall(output_dir)
            extracted = True
        # Check if it's RAR or other formats (including our temporary names)
        elif any(lower_path.endswith(ext) or (ext + ".tmp_extract") in lower_path for ext in [".rar", ".7z", ".tar", ".gz"]):
            print(f">>> [EXTRACT] Usando patool para: {os.path.basename(archive_path)}")
            patoolib.extract_archive(archive_path, outdir=output_dir, verbosity=-1)
            extracted = True
        
        if extracted:
            # Look for nested archives in the newly extracted files
            # We only look in the current output_dir to avoid infinite loops if something goes wrong
            for root, dirs, files in os.walk(output_dir):
                for f in files:
                    full_f_path = os.path.join(root, f)
                    if full_f_path == os.path.abspath(archive_path):
                        continue
                        
                    if f.lower().endswith((".zip", ".rar", ".7z", ".tar", ".gz")):
                        print(f">>> [EXTRACT] Detectado archivo anidado: {f}. Extrayendo...")
                        
                        # Use a temporary name to avoid infinite recursion if extracting into the same folder
                        temp_f_path = full_f_path + ".tmp_extract"
                        try:
                            os.rename(full_f_path, temp_f_path)
                            if extract_archive(temp_f_path, root, is_recursive=True):
                                try:
                                    os.remove(temp_f_path)
                                    print(f">>> [EXTRACT] Archivo anidado procesado y eliminado: {f}")
                                except:
                                    pass
                        except Exception as e_nested:
                            print(f">>> [EXTRACT] Error con archivo anidado {f}: {e_nested}")
                            # Try to restore name if it failed
                            if os.path.exists(temp_f_path) and not os.path.exists(full_f_path):
                                try: os.rename(temp_f_path, full_f_path)
                                except: pass
            return True
        return False
    except Exception as e:
        print(f">>> [EXTRACT] Error al extraer {os.path.basename(archive_path)}: {e}")
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
            # Soporta tanto "Title:" como "Título:"
            if line_lower.startswith("title:") or line_lower.startswith("título:"):
                prefix_len = 6 if line_lower.startswith("title:") else 7
                metadata["title"] = line[prefix_len:].strip()
            elif line_lower.startswith("hashtags:"):
                # Clean up hashtags to be a list
                raw_tags = line[9:].strip().replace('#', '').split(' ')
                metadata["tags"] = [t for t in raw_tags if t]
                # Join them back for description if needed
                metadata["description"] += line + "\n\n"
            elif line_lower.startswith("script:") or line_lower.startswith("guion:"):
                current_section = "script"
                prefix_len = 7 if line_lower.startswith("script:") else 6
                script_lines.append(line[prefix_len:].strip())
            elif current_section == "script":
                script_lines.append(line)
        
        metadata["description"] += "\n".join(script_lines)
        return metadata
    except Exception as e:
        print(f"Metadata parsing error: {e}")
        return None
