import os
import sys
from main import run_batch

def daily_generation():
    print("🚀 Iniciando Generación Diaria (Solo Generación)...")
    
    # 1. Configuración desde Variables de Entorno
    watermark = os.environ.get("WATERMARK_TEXT", "@AIShortsGenerator")
    lang = os.environ.get("LANGUAGE", "es")
    
    all_generated_folders = []
    target_count = 4
    attempts = 0
    max_total_attempts = 10 # Seguridad para evitar bucles infinitos
    
    print(f"🎯 Objetivo: {target_count} videos.")

    while len(all_generated_folders) < target_count and attempts < max_total_attempts:
        attempts += 1
        
        # Alternamos estilos para mantener el balance (0,2 = what_if | 1,3 = top_3)
        current_style = "what_if" if len(all_generated_folders) % 2 == 0 else "top_3"
        
        print(f"\n--- [Intento {attempts}] Generando Video {len(all_generated_folders) + 1}/{target_count} (Estilo: {current_style}) ---")
        
        try:
            # Intentamos generar 1 video con el estilo actual
            res = run_batch(count=1, style=current_style, watermark_text=watermark, lang=lang)
            
            if res and len(res) > 0:
                all_generated_folders.extend(res)
                print(f"✅ Video generado con éxito: {res}")
            else:
                print(f"⚠️ El intento {attempts} no produjo resultados. Reintentando...")
                
        except Exception as e:
            print(f"❌ Error en el intento {attempts}: {e}")
            import time
            time.sleep(2) # Breve espera antes de reintentar

    if len(all_generated_folders) < target_count:
        print(f"\n⚠️ Advertencia: Solo se pudieron generar {len(all_generated_folders)} videos tras {attempts} intentos.")
    else:
        print(f"\n✨ ¡Éxito! Se generaron los {target_count} videos requeridos.")

    if not all_generated_folders:
        print("❌ Error crítico: No se pudo generar ningún video.")
        sys.exit(1)

    print(f"📁 Videos listos en la carpeta 'output'. Total: {len(all_generated_folders)}")

if __name__ == "__main__":
    daily_generation()
