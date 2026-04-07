"""
Generate COMEDY, SURPRISE, and additional mood SFX + 
Generate 5 new synthetic ambient music tracks for variety.
"""
import numpy as np
import os
import struct
import random

SFX_DIR = "sfx"
MUSIC_DIR = "music"
SAMPLE_RATE = 22050

def write_wav(filename, data, sample_rate=SAMPLE_RATE, directory=SFX_DIR):
    data = np.clip(data, -1.0, 1.0)
    int_data = (data * 32767).astype(np.int16)
    filepath = os.path.join(directory, filename)
    n_samples = len(int_data)
    with open(filepath, 'wb') as f:
        f.write(b'RIFF')
        data_size = n_samples * 2
        f.write(struct.pack('<I', 36 + data_size))
        f.write(b'WAVE')
        f.write(b'fmt ')
        f.write(struct.pack('<I', 16))
        f.write(struct.pack('<H', 1))
        f.write(struct.pack('<H', 1))
        f.write(struct.pack('<I', sample_rate))
        f.write(struct.pack('<I', sample_rate * 2))
        f.write(struct.pack('<H', 2))
        f.write(struct.pack('<H', 16))
        f.write(b'data')
        f.write(struct.pack('<I', data_size))
        f.write(int_data.tobytes())
    print(f"  Generated: {directory}/{filename} ({n_samples/sample_rate:.1f}s)")

def fade_in_out(data, fi=0.05, fo=0.2, sr=SAMPLE_RATE):
    n = len(data)
    fin = int(fi * sr)
    fon = int(fo * sr)
    if fin > 0 and fin < n: data[:fin] *= np.linspace(0, 1, fin)
    if fon > 0 and fon < n: data[-fon:] *= np.linspace(1, 0, fon)
    return data

# =============================================
# COMEDY / HUMOR SFX
# =============================================

def generate_comedy_boing(duration=0.5):
    """Cartoon boing/spring sound for funny moments."""
    t = np.linspace(0, duration, int(duration * SAMPLE_RATE), endpoint=False)
    freq = 400 * np.exp(-3 * t) + 200
    phase = np.cumsum(freq) / SAMPLE_RATE * 2 * np.pi
    signal = np.sin(phase) * 0.4
    signal += np.sin(phase * 2) * 0.15  # Harmonic for cartooniness
    env = np.exp(-4 * t / duration)
    signal *= env
    # Add "wobble"
    wobble = np.sin(2 * np.pi * 8 * t) * 0.15 * env
    signal += wobble
    return fade_in_out(signal, 0.005, 0.1)

def generate_comedy_slide(duration=0.6):
    """Slide whistle going up - classic comedy."""
    t = np.linspace(0, duration, int(duration * SAMPLE_RATE), endpoint=False)
    freq = 200 + 1200 * (t/duration)**2
    phase = np.cumsum(freq) / SAMPLE_RATE * 2 * np.pi
    signal = np.sin(phase) * 0.3
    env = np.sin(np.pi * t / duration)
    signal *= env
    return fade_in_out(signal, 0.01, 0.1)

def generate_comedy_honk(duration=0.3):
    """Quick honk/toot for punchlines."""
    t = np.linspace(0, duration, int(duration * SAMPLE_RATE), endpoint=False)
    signal = np.sin(2 * np.pi * 280 * t) * 0.3
    signal += np.sin(2 * np.pi * 350 * t) * 0.2
    # Add nasal quality
    signal = np.tanh(signal * 3) * 0.3
    env = np.exp(-3 * t / duration)
    signal *= env
    return fade_in_out(signal, 0.005, 0.05)

def generate_record_scratch(duration=0.4):
    """Record scratch for "wait what?" moments."""
    t = np.linspace(0, duration, int(duration * SAMPLE_RATE), endpoint=False)
    # Descending pitch
    freq = 2000 * np.exp(-8 * t)
    phase = np.cumsum(freq) / SAMPLE_RATE * 2 * np.pi
    signal = np.sin(phase) * 0.2
    # Add scratchy noise
    noise = np.random.normal(0, 0.3, len(t))
    noise *= np.exp(-5 * t)
    signal += noise
    return fade_in_out(signal, 0.005, 0.05)

# =============================================
# SURPRISE / WOW SFX
# =============================================

def generate_surprise_sting(duration=0.8):
    """'DUN DUN DUN' style reveal hit."""
    t = np.linspace(0, duration, int(duration * SAMPLE_RATE), endpoint=False)
    # Three quick hits
    hit1 = np.sin(2 * np.pi * 150 * t) * np.exp(-8 * t) * 0.5
    # Second hit offset
    t2 = np.maximum(t - 0.2, 0)
    hit2 = np.sin(2 * np.pi * 120 * t) * np.exp(-8 * t2) * 0.4 * (t > 0.2)
    # Third hit (lowest, longest)
    t3 = np.maximum(t - 0.4, 0)
    hit3 = np.sin(2 * np.pi * 80 * t) * np.exp(-4 * t3) * 0.6 * (t > 0.4)
    signal = hit1 + hit2 + hit3
    return fade_in_out(signal, 0.005, 0.2)

def generate_wow_riser(duration=1.2):
    """Ascending 'wow' sound for mind-blowing facts."""
    t = np.linspace(0, duration, int(duration * SAMPLE_RATE), endpoint=False)
    freq = 150 + 1500 * (t/duration)**3
    phase = np.cumsum(freq) / SAMPLE_RATE * 2 * np.pi
    signal = np.sin(phase) * 0.25
    signal += np.sin(phase * 1.5) * 0.1  # Fifth harmony
    env = (t/duration)**0.5 * np.exp(-0.5 * (1 - t/duration))
    signal *= env
    # Sparkle at the top
    sparkle = np.sin(2 * np.pi * 5000 * t) * 0.05 * (t/duration)**3
    signal += sparkle
    return fade_in_out(signal, 0.1, 0.2)

# =============================================
# GENERATE NEW MUSIC TRACKS (Synthetic ambient)
# =============================================

def generate_music_track(name, bpm, key_freq, mood_type, duration=120):
    """Generate a synthetic ambient music track."""
    sr = 22050
    t = np.linspace(0, duration, int(duration * sr), endpoint=False)
    signal = np.zeros_like(t)
    
    beat_dur = 60.0 / bpm
    
    if mood_type == "dark_ambient":
        # Low drone + dissonant harmonics
        signal += np.sin(2 * np.pi * key_freq * t) * 0.08
        signal += np.sin(2 * np.pi * key_freq * 1.06 * t) * 0.04  # Minor 2nd
        signal += np.sin(2 * np.pi * key_freq * 0.5 * t) * 0.06   # Sub octave
        # Slow evolving pad
        mod = 0.5 + 0.5 * np.sin(2 * np.pi * 0.05 * t)
        signal *= mod
        # Add filtered noise texture
        noise = np.random.normal(0, 0.02, len(t))
        kernel = np.ones(500) / 500
        noise = np.convolve(noise, kernel, mode='same')
        signal += noise
        
    elif mood_type == "upbeat":
        # Rhythmic pulse with bright harmonics
        pulse = (np.sin(2 * np.pi * t / beat_dur * np.pi) > 0.7).astype(float) * 0.05
        signal += np.sin(2 * np.pi * key_freq * t) * 0.06
        signal += np.sin(2 * np.pi * key_freq * 1.5 * t) * 0.03  # Fifth
        signal += np.sin(2 * np.pi * key_freq * 2 * t) * 0.02     # Octave
        signal += pulse * np.sin(2 * np.pi * key_freq * 4 * t)
        
    elif mood_type == "epic_cinematic":
        # Power chords + slow rhythm
        signal += np.sin(2 * np.pi * key_freq * t) * 0.08
        signal += np.sin(2 * np.pi * key_freq * 1.5 * t) * 0.05  # Fifth
        signal += np.sin(2 * np.pi * key_freq * 2 * t) * 0.04    # Octave
        # Slow swell every 4 beats
        swell = 0.5 + 0.5 * np.sin(2 * np.pi * t / (beat_dur * 4))
        signal *= swell
        # Low rumble
        signal += np.sin(2 * np.pi * 30 * t) * 0.03 * swell
        
    elif mood_type == "mysterious":
        # Whole-tone scale intervals
        signal += np.sin(2 * np.pi * key_freq * t) * 0.06
        signal += np.sin(2 * np.pi * key_freq * 1.26 * t) * 0.04  # Major 3rd
        signal += np.sin(2 * np.pi * key_freq * 1.414 * t) * 0.03 # Tritone
        # Slow evolving texture
        lfo = 0.5 + 0.5 * np.sin(2 * np.pi * 0.1 * t)
        signal *= lfo
        # Gentle high shimmer
        shimmer = np.sin(2 * np.pi * key_freq * 8 * t) * 0.01 * lfo
        signal += shimmer
        
    elif mood_type == "emotional":
        # Minor key pad
        signal += np.sin(2 * np.pi * key_freq * t) * 0.07
        signal += np.sin(2 * np.pi * key_freq * 1.2 * t) * 0.05  # Minor 3rd  
        signal += np.sin(2 * np.pi * key_freq * 1.5 * t) * 0.03  # Fifth
        # Slow tremolo for emotion
        tremolo = 0.7 + 0.3 * np.sin(2 * np.pi * 3 * t)
        signal *= tremolo
        # Gentle volume swell
        swell = 0.5 + 0.5 * np.sin(2 * np.pi * 0.03 * t)
        signal *= swell
    
    # Master fade in/out
    signal = fade_in_out(signal, 3.0, 3.0, sr)
    
    # Normalize
    peak = np.max(np.abs(signal))
    if peak > 0:
        signal = signal / peak * 0.7
    
    write_wav(name, signal, sr, MUSIC_DIR)

if __name__ == "__main__":
    os.makedirs(SFX_DIR, exist_ok=True)
    os.makedirs(MUSIC_DIR, exist_ok=True)
    
    print("😂 COMEDY / HUMOR SFX...")
    for i in range(3):
        write_wav(f"comedy_boing_{i+1}.wav", generate_comedy_boing(random.uniform(0.4, 0.6)))
    for i in range(2):
        write_wav(f"comedy_slide_{i+1}.wav", generate_comedy_slide(random.uniform(0.5, 0.7)))
    for i in range(2):
        write_wav(f"comedy_honk_{i+1}.wav", generate_comedy_honk(random.uniform(0.2, 0.4)))
    for i in range(2):
        write_wav(f"record_scratch_{i+1}.wav", generate_record_scratch(random.uniform(0.3, 0.5)))
    
    print("\n🤯 SURPRISE / WOW SFX...")
    for i in range(3):
        write_wav(f"surprise_sting_{i+1}.wav", generate_surprise_sting(random.uniform(0.6, 1.0)))
    for i in range(2):
        write_wav(f"wow_riser_{i+1}.wav", generate_wow_riser(random.uniform(1.0, 1.5)))
    
    print("\n🎵 GENERATING NEW MUSIC TRACKS...")
    generate_music_track("dark_tension.wav", 70, 55, "dark_ambient", 90)
    generate_music_track("upbeat_energy.wav", 120, 220, "upbeat", 90)
    generate_music_track("epic_battle.wav", 80, 82, "epic_cinematic", 90)
    generate_music_track("deep_mystery.wav", 60, 110, "mysterious", 90)
    generate_music_track("emotional_piano.wav", 72, 165, "emotional", 90)
    
    print("\n✅ All comedy SFX + music tracks generated!")
