import asyncio
import os
from src.tts_engine import generate_audio
from src.video_editor import create_karaoke_clips
from moviepy.editor import ColorClip, AudioFileClip, CompositeVideoClip, concatenate_videoclips

async def run_fast_test():
    text = "Hola, esto es una prueba rápida de sincronización de subtítulos. Necesito saber si las palabras aparecen exactamente cuando hablo. El destiempo es el enemigo."
    output_dir = "output/fast_test"
    os.makedirs(output_dir, exist_ok=True)
    audio_path = os.path.join(output_dir, "test_audio.mp3")
    
    print("🎙️ Generando TTS...")
    success, timings = await generate_audio(text, audio_path, voice="es-ES-AlvaroNeural")
    
    if success and not timings:
        print("⚠️ TTS no devolvió tiempos. Usando Whisper Aligner...")
        from src.aligner import get_word_timings
        timings = get_word_timings(audio_path, text_hint=text)
        
        print("✅ Tiempos recuperados con stable-ts de forma nativa")
    
    if not success or not timings:
        print("❌ Error generando audio o sin tiempos.")
        return
        
    print(f"✅ Tiempos generados: {len(timings)} palabras.")
    # Show first 3 timings to debug
    for t in timings[:3]:
        print(f"  - {t['word']} ({t['start']:.2f}s -> {t['end']:.2f}s)")
        
    print("🎬 Cargando Audio Clip...")
    audio_clip = AudioFileClip(audio_path)
    duration = audio_clip.duration
    
    # Create black background
    bg_clip = ColorClip(size=(1080, 1920), color=(0,0,0)).set_duration(duration)
    
    print("📝 Generando Clips de Video/Texto...")
    # Generate Karaokes
    text_clips = create_karaoke_clips(
        timings, 
        duration, 
        0, # start offset
        width=1080, 
        height=1920, 
        raw_text=text,
        is_header=True
    )
    
    print("🎞️ Ensamblando Video...")
    final_video = CompositeVideoClip([bg_clip] + text_clips, size=(1080, 1920))
    final_video = final_video.set_audio(audio_clip)
    
    out_file = os.path.join(output_dir, "fast_sync_test.mp4")
    print(f"💾 Guardando {out_file}...")
    final_video.write_videofile(
        out_file, 
        fps=30, 
        codec="libx264", 
        audio_codec="aac", 
        preset="ultrafast",
        logger=None # Hide moviepy progress bar to keep it clean
    )
    print("✅ TEST TERMINADO. ¡Abre output/fast_test/fast_sync_test.mp4 y mira la sincro!")

if __name__ == "__main__":
    asyncio.run(run_fast_test())
