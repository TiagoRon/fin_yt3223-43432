"""
Generate ambient textures and SFX programmatically using numpy + scipy.
These are subtle, non-annoying sound effects designed for short-form video content.
"""
import numpy as np
import os
import struct
import random

SFX_DIR = "sfx"
SAMPLE_RATE = 22050  # Lower sample rate = smaller files, good enough for SFX

def write_wav(filename, data, sample_rate=SAMPLE_RATE):
    """Write a numpy float array (-1 to 1) as a 16-bit WAV file."""
    data = np.clip(data, -1.0, 1.0)
    int_data = (data * 32767).astype(np.int16)
    
    filepath = os.path.join(SFX_DIR, filename)
    n_samples = len(int_data)
    
    with open(filepath, 'wb') as f:
        # WAV header
        f.write(b'RIFF')
        data_size = n_samples * 2  # 16-bit = 2 bytes per sample
        f.write(struct.pack('<I', 36 + data_size))  # File size - 8
        f.write(b'WAVE')
        f.write(b'fmt ')
        f.write(struct.pack('<I', 16))  # Chunk size
        f.write(struct.pack('<H', 1))   # PCM format
        f.write(struct.pack('<H', 1))   # Mono
        f.write(struct.pack('<I', sample_rate))
        f.write(struct.pack('<I', sample_rate * 2))  # Byte rate
        f.write(struct.pack('<H', 2))   # Block align
        f.write(struct.pack('<H', 16))  # Bits per sample
        f.write(b'data')
        f.write(struct.pack('<I', data_size))
        f.write(int_data.tobytes())
    
    print(f"  ✅ Generated: {filename} ({n_samples/sample_rate:.1f}s)")

def fade_in_out(data, fade_in=0.1, fade_out=0.3):
    """Apply fade in/out to avoid clicks."""
    n = len(data)
    fi = int(fade_in * SAMPLE_RATE)
    fo = int(fade_out * SAMPLE_RATE)
    if fi > 0:
        data[:fi] *= np.linspace(0, 1, fi)
    if fo > 0:
        data[-fo:] *= np.linspace(1, 0, fo)
    return data

# =============================================
# 1. AMBIENT TEXTURES (Loopable backgrounds)
# =============================================

def generate_ambient_drone(duration=8.0, base_freq=80):
    """Deep, warm drone - gives a cinematic 'weight' to the video."""
    t = np.linspace(0, duration, int(duration * SAMPLE_RATE), endpoint=False)
    
    # Multiple harmonics for warmth
    signal = np.sin(2 * np.pi * base_freq * t) * 0.4
    signal += np.sin(2 * np.pi * base_freq * 1.5 * t) * 0.2
    signal += np.sin(2 * np.pi * base_freq * 2.0 * t) * 0.1
    
    # Slow LFO modulation for movement
    lfo = 0.7 + 0.3 * np.sin(2 * np.pi * 0.15 * t)
    signal *= lfo
    
    # Add subtle noise texture
    noise = np.random.normal(0, 0.02, len(t))
    signal += noise
    
    return fade_in_out(signal, fade_in=1.0, fade_out=1.0)

def generate_ambient_wind(duration=8.0):
    """Filtered noise that sounds like soft wind/atmosphere."""
    t = np.linspace(0, duration, int(duration * SAMPLE_RATE), endpoint=False)
    
    # Pink-ish noise (filtered white noise)
    noise = np.random.normal(0, 0.3, len(t))
    
    # Simple low-pass filter using moving average
    kernel_size = 150
    kernel = np.ones(kernel_size) / kernel_size
    filtered = np.convolve(noise, kernel, mode='same')
    
    # Slow volume modulation (breathing effect)
    mod = 0.5 + 0.5 * np.sin(2 * np.pi * 0.08 * t)
    filtered *= mod
    
    return fade_in_out(filtered * 0.6, fade_in=1.0, fade_out=1.0)

def generate_ambient_space(duration=8.0):
    """Ethereal space ambience - slow shimmering tones."""
    t = np.linspace(0, duration, int(duration * SAMPLE_RATE), endpoint=False)
    
    # Multiple detuned sine waves creating a pad
    freqs = [220, 221.5, 330, 331.2, 440, 441.8]
    signal = np.zeros_like(t)
    for f in freqs:
        signal += np.sin(2 * np.pi * f * t) * 0.1
    
    # Slow tremolo
    trem = 0.6 + 0.4 * np.sin(2 * np.pi * 0.1 * t)
    signal *= trem
    
    # Add subtle high shimmer
    shimmer = np.sin(2 * np.pi * 1200 * t) * 0.02 * np.sin(2 * np.pi * 0.3 * t)
    signal += shimmer
    
    return fade_in_out(signal, fade_in=1.5, fade_out=1.5)

# =============================================
# 2. TRANSITION SFX (Short, punchy)
# =============================================

def generate_swoosh(duration=0.5):
    """Quick swoosh/swipe sound for scene transitions."""
    t = np.linspace(0, duration, int(duration * SAMPLE_RATE), endpoint=False)
    
    # Frequency sweep from high to low
    freq = np.linspace(3000, 200, len(t))
    phase = np.cumsum(freq) / SAMPLE_RATE * 2 * np.pi
    signal = np.sin(phase) * 0.3
    
    # Add noise texture 
    noise = np.random.normal(0, 0.15, len(t))
    # Quick low-pass
    kernel = np.ones(30) / 30
    noise = np.convolve(noise, kernel, mode='same')
    signal += noise
    
    # Sharp envelope
    env = np.exp(-3 * t / duration)
    signal *= env
    
    return fade_in_out(signal, fade_in=0.01, fade_out=0.1)

def generate_shimmer(duration=0.8):
    """Bright, sparkly shimmer for text reveals or highlights."""
    t = np.linspace(0, duration, int(duration * SAMPLE_RATE), endpoint=False)
    
    # High frequency content with harmonics
    signal = np.sin(2 * np.pi * 2500 * t) * 0.15
    signal += np.sin(2 * np.pi * 3750 * t) * 0.10
    signal += np.sin(2 * np.pi * 5000 * t) * 0.05
    
    # Envelope: quick attack, slow decay
    env = np.exp(-2.5 * t / duration)
    signal *= env
    
    # Add metallic texture
    metal = np.sin(2 * np.pi * 4200 * t) * np.sin(2 * np.pi * 7 * t) * 0.08
    signal += metal * env
    
    return fade_in_out(signal, fade_in=0.01, fade_out=0.2)

def generate_bass_drop(duration=0.6):
    """Sub-bass hit for dramatic moments."""
    t = np.linspace(0, duration, int(duration * SAMPLE_RATE), endpoint=False)
    
    # Descending frequency
    freq = 150 * np.exp(-3 * t / duration) + 40
    phase = np.cumsum(freq) / SAMPLE_RATE * 2 * np.pi
    signal = np.sin(phase) * 0.7
    
    # Sharp percussive envelope
    env = np.exp(-5 * t / duration)
    signal *= env
    
    return fade_in_out(signal, fade_in=0.005, fade_out=0.15)

def generate_tension_riser(duration=2.0):
    """Slow rising pitch that creates anticipation (subtle, not aggressive)."""
    t = np.linspace(0, duration, int(duration * SAMPLE_RATE), endpoint=False)
    
    # Slowly rising frequency
    freq = 200 + 800 * (t / duration) ** 2
    phase = np.cumsum(freq) / SAMPLE_RATE * 2 * np.pi
    signal = np.sin(phase) * 0.2
    
    # Rising volume envelope
    env = (t / duration) ** 1.5
    signal *= env
    
    # Add filtered noise rising with it
    noise = np.random.normal(0, 0.1, len(t))
    kernel = np.ones(80) / 80
    noise = np.convolve(noise, kernel, mode='same')
    noise *= env * 0.5
    signal += noise
    
    return fade_in_out(signal, fade_in=0.3, fade_out=0.1)

def generate_subtle_click(duration=0.08):
    """Tiny click/tick for subtitle word changes."""
    t = np.linspace(0, duration, int(duration * SAMPLE_RATE), endpoint=False)
    
    # Very short burst
    signal = np.sin(2 * np.pi * 1000 * t) * 0.5
    env = np.exp(-40 * t)
    signal *= env
    
    return signal

def generate_deep_boom(duration=1.0):
    """Deep cinematic boom for intro/outro."""
    t = np.linspace(0, duration, int(duration * SAMPLE_RATE), endpoint=False)
    
    # Low frequency hit
    signal = np.sin(2 * np.pi * 50 * t) * 0.8
    signal += np.sin(2 * np.pi * 100 * t) * 0.4
    
    # Percussive envelope
    env = np.exp(-4 * t)
    signal *= env
    
    # Add initial transient
    transient = np.random.normal(0, 0.3, min(500, len(t)))
    transient *= np.exp(-30 * np.linspace(0, 1, len(transient)))
    signal[:len(transient)] += transient
    
    return fade_in_out(signal, fade_in=0.002, fade_out=0.3)

def generate_reverse_cymbal(duration=1.5):
    """Reverse cymbal swell - great for building tension before a scene."""
    t = np.linspace(0, duration, int(duration * SAMPLE_RATE), endpoint=False)
    
    # High frequency noise
    noise = np.random.normal(0, 0.4, len(t))
    
    # Band-pass-ish filter
    kernel = np.ones(20) / 20
    filtered = np.convolve(noise, kernel, mode='same')
    
    # Rising envelope (reverse of cymbal decay)
    env = (t / duration) ** 3
    filtered *= env
    
    return fade_in_out(filtered, fade_in=0.5, fade_out=0.05)

# =============================================
# MAIN: Generate all SFX
# =============================================

if __name__ == "__main__":
    os.makedirs(SFX_DIR, exist_ok=True)
    
    print("🔊 Generating Ambient Textures...")
    for i in range(3):
        base = random.choice([60, 70, 80, 90, 100])
        write_wav(f"ambient_drone_{i+1}.wav", generate_ambient_drone(duration=8.0, base_freq=base))
    
    for i in range(2):
        write_wav(f"ambient_wind_{i+1}.wav", generate_ambient_wind(duration=8.0))
    
    for i in range(2):
        write_wav(f"ambient_space_{i+1}.wav", generate_ambient_space(duration=8.0))
    
    print("\n🎬 Generating Transition SFX...")
    for i in range(3):
        write_wav(f"swoosh_gen_{i+1}.wav", generate_swoosh(duration=random.uniform(0.3, 0.6)))
    
    for i in range(3):
        write_wav(f"shimmer_gen_{i+1}.wav", generate_shimmer(duration=random.uniform(0.6, 1.0)))
    
    for i in range(2):
        write_wav(f"bass_drop_gen_{i+1}.wav", generate_bass_drop(duration=random.uniform(0.4, 0.7)))
    
    for i in range(2):
        write_wav(f"tension_riser_gen_{i+1}.wav", generate_tension_riser(duration=random.uniform(1.5, 2.5)))
    
    for i in range(3):
        write_wav(f"click_gen_{i+1}.wav", generate_subtle_click(duration=0.08))
    
    for i in range(2):
        write_wav(f"boom_gen_{i+1}.wav", generate_deep_boom(duration=random.uniform(0.8, 1.2)))
    
    for i in range(2):
        write_wav(f"reverse_cymbal_gen_{i+1}.wav", generate_reverse_cymbal(duration=random.uniform(1.2, 2.0)))
    
    print("\n✅ All SFX generated successfully!")
    print(f"📂 Files saved to: {os.path.abspath(SFX_DIR)}")
