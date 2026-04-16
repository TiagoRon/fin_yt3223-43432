import os
import sys
from main import run_batch

def daily_generation():
    print("🚀 Iniciando Generación Diaria (Solo Generación)...")
    
    # 1. Configuración desde Variables de Entorno
    watermark = os.environ.get("WATERMARK_TEXT", "@AIShortsGenerator")
    lang = os.environ.get("LANGUAGE", "es")
    
    all_generated_folders = []

    # 2. Generar Video 'Top 3'
    print("\n--- Generando Video: TOP 3 ---")
    try:
        res_top3 = run_batch(count=1, style="top_3", watermark_text=watermark, lang=lang)
        if res_top3:
            all_generated_folders.extend(res_top3)
            print(f"✅ Top 3 Generado: {res_top3}")
    except Exception as e:
        print(f"❌ Error generando Top 3: {e}")

    # 3. Generar Video 'What If'
    print("\n--- Generando Video: WHAT IF ---")
    try:
        res_whatif = run_batch(count=1, style="what_if", watermark_text=watermark, lang=lang)
        if res_whatif:
            all_generated_folders.extend(res_whatif)
            print(f"✅ What If Generado: {res_whatif}")
    except Exception as e:
        print(f"❌ Error generando What If: {e}")

    if not all_generated_folders:
        print("❌ No se generaron videos. Revisa los logs.")
        sys.exit(1)

    print("\n✅ Generación Diaria Finalizada. Revisa la carpeta 'output'.")

if __name__ == "__main__":
    daily_generation()
