import os
import sys
from main import run_batch

def daily_generation():
    print("🚀 Iniciando Generación Diaria (Solo Generación)...")
    
    # 1. Configuración desde Variables de Entorno
    watermark = os.environ.get("WATERMARK_TEXT", "@AIShortsGenerator")
    lang = os.environ.get("LANGUAGE", "es")
    
    all_generated_folders = []
    
    # Lista de estilos: 2 'what_if' y 2 'top_3' para un total de 4 videos
    styles = ["what_if", "what_if", "top_3", "top_3"]

    for style in styles:
        print(f"\n--- Generando Video: {style.upper().replace('_', ' ')} ---")
        try:
            res = run_batch(count=1, style=style, watermark_text=watermark, lang=lang)
            if res:
                all_generated_folders.extend(res)
                print(f"✅ {style.capitalize()} Generado: {res}")
        except Exception as e:
            print(f"❌ Error generando {style}: {e}")

    if not all_generated_folders:
        print("❌ No se generaron videos. Revisa los logs.")
        sys.exit(1)

    print(f"\n✅ Generación Diaria Finalizada. Total: {len(all_generated_folders)} videos.")
    print("Revisa la carpeta 'output'.")

if __name__ == "__main__":
    daily_generation()
