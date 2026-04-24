import os
import sys
from main import run_batch

def daily_generation():
    print("🚀 Iniciando Generación Diaria (Solo Generación)...")
    
    # 1. Configuración desde Variables de Entorno
    watermark = os.environ.get("WATERMARK_TEXT", "@AIShortsGenerator")
    lang = os.environ.get("LANGUAGE", "es")
    
    all_generated_folders = []
    
    # Lista de estilos para rotar (uno cada 6 horas = 4 videos al día)
    styles = ["top_3", "what_if", "curiosity", "dark_facts"]
    
    # Seleccionar estilo según la hora actual (0-5: top_3, 6-11: what_if, etc)
    from datetime import datetime
    hour = datetime.now().hour
    style_index = (hour // 6) % len(styles)
    selected_style = styles[style_index]
    
    print(f"\n--- Generando Video: {selected_style.upper().replace('_', ' ')} (Hora: {hour}:00) ---")
    try:
        res = run_batch(count=1, style=selected_style, watermark_text=watermark, lang=lang)
        if res:
            all_generated_folders.extend(res)
            print(f"✅ {selected_style.capitalize()} Generado: {res}")
    except Exception as e:
        print(f"❌ Error generando {selected_style}: {e}")

    if not all_generated_folders:
        print("❌ No se generaron videos. Revisa los logs.")
        sys.exit(1)

    print(f"\n✅ Generación Diaria Finalizada. Total: {len(all_generated_folders)} videos.")
    print("Revisa la carpeta 'output'.")

if __name__ == "__main__":
    daily_generation()
