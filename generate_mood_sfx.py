"""
Generate MOOD-SPECIFIC sound effects for contextual audio design.
These SFX are triggered by scene content: horror stingers, suspense drones,
epic hits, mystery tones, eerie textures, dramatic reveals, etc.
"""
import numpy as np
import os
import struct
import random

SFX_DIR = "sfx"
SAMPLE_RATE = 22050

def write_wav(filename, data, sample_rate=SAMPLE_RATE):
    """Write a numpy float array (-1 to 1) as a 16-bit WAV file."""
    data = np.clip(data, -1.0, 1.0)
    int_data = (data * 32767).astype(np.int16)
    filepath = os.path.join(SFX_DIR, filename)
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
    print(f"  Generated: {filename} ({n_samples/sample_rate:.1f}s)")

def fade_in_out(data, fade_in=0.05, fade_out=0.2):
    n = len(data)
    fi = int(fade_in * SAMPLE_RATE)
    fo = int(fade_out * SAMPLE_RATE)
    if fi > 0 and fi < n: data[:fi] *= np.linspace(0, 1, fi)
    if fo > 0 and fo < n: data[-fo:] *= np.linspace(1, 0, fo)
    return data

# =============================================
# HORROR / TERROR SFX
# =============================================

def generate_horror_stinger(duration=1.5):
    """Sharp, unsettling stinger for scary moments - like a violin screech."""
    t = np.linspace(0, duration, int(duration * SAMPLE_RATE), endpoint=False)
    # Dissonant cluster of close frequencies
    signal = np.sin(2 * np.pi * 440 * t) * 0.2
    signal += np.sin(2 * np.pi * 466 * t) * 0.2  # Minor 2nd = dissonance
    signal += np.sin(2 * np.pi * 554 * t) * 0.15  # Augmented = tension
    # Quick attack, medium decay
    env = np.exp(-2 * t / duration)
    signal *= env
    # Add scratchy noise
    noise = np.random.normal(0, 0.05, len(t)) * env
    signal += noise
    return fade_in_out(signal, 0.01, 0.3)

def generate_horror_whisper(duration=2.0):
    """Eerie breathy texture for creepy moments."""
    t = np.linspace(0, duration, int(duration * SAMPLE_RATE), endpoint=False)
    # Filtered noise (breathy)
    noise = np.random.normal(0, 0.3, len(t))
    kernel = np.ones(100) / 100
    filtered = np.convolve(noise, kernel, mode='same')
    # Modulated by slow sine for "breathing" effect
    mod = 0.5 + 0.5 * np.sin(2 * np.pi * 0.5 * t)
    filtered *= mod
    # Add very low sub-rumble
    sub = np.sin(2 * np.pi * 35 * t) * 0.15 * (1 - t/duration)
    return fade_in_out(filtered * 0.4 + sub, 0.3, 0.5)

def generate_horror_impact(duration=0.8):
    """Deep, disturbing thud/impact for revelations."""
    t = np.linspace(0, duration, int(duration * SAMPLE_RATE), endpoint=False)
    # Very low hit
    signal = np.sin(2 * np.pi * 35 * t) * 0.8
    signal += np.sin(2 * np.pi * 70 * t) * 0.3
    # Distorted crunch
    signal += np.tanh(np.random.normal(0, 0.5, len(t))) * 0.2 * np.exp(-10*t)
    env = np.exp(-5 * t)
    signal *= env
    return fade_in_out(signal, 0.002, 0.2)

# =============================================
# MYSTERY / SUSPENSE SFX
# =============================================

def generate_mystery_tone(duration=2.0):
    """Ethereal, questioning tone for mystery reveals."""
    t = np.linspace(0, duration, int(duration * SAMPLE_RATE), endpoint=False)
    # Whole-tone scale interval (dreamy/uncertain)
    signal = np.sin(2 * np.pi * 330 * t) * 0.2
    signal += np.sin(2 * np.pi * 415 * t) * 0.15  # Tritone = mystery
    signal += np.sin(2 * np.pi * 523 * t) * 0.1
    # Slow shimmer
    mod = 0.7 + 0.3 * np.sin(2 * np.pi * 2 * t)
    signal *= mod
    env = np.ones_like(t)
    env[:int(0.3*SAMPLE_RATE)] = np.linspace(0, 1, int(0.3*SAMPLE_RATE))
    env[-int(0.5*SAMPLE_RATE):] = np.linspace(1, 0, int(0.5*SAMPLE_RATE))
    signal *= env
    return signal

def generate_suspense_build(duration=2.5):
    """Rising tension that builds anxiety."""
    t = np.linspace(0, duration, int(duration * SAMPLE_RATE), endpoint=False)
    # Rising frequency
    freq = 100 + 600 * (t/duration)**2
    phase = np.cumsum(freq) / SAMPLE_RATE * 2 * np.pi
    signal = np.sin(phase) * 0.15
    # Rising noise floor
    noise = np.random.normal(0, 0.1, len(t))
    kernel = np.ones(60) / 60
    noise = np.convolve(noise, kernel, mode='same')
    noise *= (t/duration)**2 * 0.5
    signal += noise
    # Rising volume
    signal *= (t/duration)**1.5
    return fade_in_out(signal, 0.5, 0.05)

# =============================================
# EPIC / DRAMATIC SFX
# =============================================

def generate_epic_hit(duration=1.2):
    """Cinematic orchestral hit for dramatic statements."""
    t = np.linspace(0, duration, int(duration * SAMPLE_RATE), endpoint=False)
    # Power chord: root + fifth + octave
    signal = np.sin(2 * np.pi * 110 * t) * 0.4
    signal += np.sin(2 * np.pi * 165 * t) * 0.3
    signal += np.sin(2 * np.pi * 220 * t) * 0.2
    signal += np.sin(2 * np.pi * 55 * t) * 0.3  # Sub for weight
    # Sharp transient + slow tail
    env = 0.3 * np.exp(-0.5 * t) + 0.7 * np.exp(-8 * t)
    signal *= env
    # Crash noise burst at start
    crash = np.random.normal(0, 0.3, min(2000, len(t)))
    crash *= np.exp(-20 * np.linspace(0, 1, len(crash)))
    signal[:len(crash)] += crash
    return fade_in_out(signal, 0.002, 0.3)

def generate_dramatic_reveal(duration=1.8):
    """Ascending 'reveal' sound for surprising facts."""
    t = np.linspace(0, duration, int(duration * SAMPLE_RATE), endpoint=False)
    # Ascending arpeggio-like sweep
    freq = 200 + 800 * np.sin(np.pi * t / duration / 2)  # Sine curve up
    phase = np.cumsum(freq) / SAMPLE_RATE * 2 * np.pi
    signal = np.sin(phase) * 0.25
    # Add harmonic layers
    signal += np.sin(phase * 2) * 0.1
    signal += np.sin(phase * 3) * 0.05
    # Bell-like envelope
    env = np.sin(np.pi * t / duration) ** 0.5
    signal *= env
    # Add shimmer
    shimmer = np.sin(2 * np.pi * 3000 * t) * 0.03 * env
    signal += shimmer
    return fade_in_out(signal, 0.05, 0.4)

# =============================================
# CURIOSITY / SCIENCE SFX
# =============================================

def generate_digital_blip(duration=0.4):
    """Short electronic blip for facts/data moments."""
    t = np.linspace(0, duration, int(duration * SAMPLE_RATE), endpoint=False)
    freq = 800 + 400 * np.sin(2 * np.pi * 5 * t)
    phase = np.cumsum(freq) / SAMPLE_RATE * 2 * np.pi
    signal = np.sin(phase) * 0.3
    env = np.exp(-6 * t / duration)
    signal *= env
    return fade_in_out(signal, 0.005, 0.05)

def generate_sci_fi_scan(duration=1.0):
    """Scanning/processing sound for science/tech content."""
    t = np.linspace(0, duration, int(duration * SAMPLE_RATE), endpoint=False)
    # Frequency oscillates rapidly
    freq = 600 + 400 * np.sin(2 * np.pi * 8 * t)
    phase = np.cumsum(freq) / SAMPLE_RATE * 2 * np.pi
    signal = np.sin(phase) * 0.2
    # Add digital artifacts
    step_signal = np.sin(2 * np.pi * 1200 * t) * 0.1
    step_signal *= (np.sin(2 * np.pi * 15 * t) > 0).astype(float)
    signal += step_signal
    env = np.sin(np.pi * t / duration)
    signal *= env
    return fade_in_out(signal, 0.02, 0.1)

# =============================================
# SAD / EMOTIONAL SFX
# =============================================

def generate_sad_tone(duration=2.0):
    """Melancholic descending tone for emotional moments."""
    t = np.linspace(0, duration, int(duration * SAMPLE_RATE), endpoint=False)
    # Descending minor interval
    freq = 440 * np.exp(-0.3 * t / duration)
    phase = np.cumsum(freq) / SAMPLE_RATE * 2 * np.pi
    signal = np.sin(phase) * 0.2
    # Minor third harmony descending
    freq2 = 523 * np.exp(-0.3 * t / duration)
    phase2 = np.cumsum(freq2) / SAMPLE_RATE * 2 * np.pi
    signal += np.sin(phase2) * 0.12
    # Slow tremolo (emotion)
    trem = 0.7 + 0.3 * np.sin(2 * np.pi * 4 * t)
    signal *= trem
    env = np.sin(np.pi * t / duration) ** 0.7
    signal *= env
    return signal

# =============================================
# NATURE / ENVIRONMENT STINGERS
# =============================================

def generate_thunder(duration=2.0):
    """Rumbling thunder for dramatic/dark moments."""
    t = np.linspace(0, duration, int(duration * SAMPLE_RATE), endpoint=False)
    # White noise burst → filtered rumble
    noise = np.random.normal(0, 0.5, len(t))
    # Heavy low-pass
    kernel = np.ones(300) / 300
    rumble = np.convolve(noise, kernel, mode='same')
    # Initial crack
    crack = np.random.normal(0, 0.8, min(3000, len(t)))
    crack *= np.exp(-15 * np.linspace(0, 1, len(crack)))
    rumble[:len(crack)] += crack
    # Decay envelope with some rumble
    env = np.exp(-1.5 * t / duration)
    env += 0.3 * np.sin(2 * np.pi * 0.7 * t) * np.exp(-2 * t / duration)
    rumble *= env
    return fade_in_out(rumble * 0.6, 0.01, 0.5)

# =============================================
# MAIN: Generate all mood-specific SFX
# =============================================

if __name__ == "__main__":
    os.makedirs(SFX_DIR, exist_ok=True)
    
    print("🎃 HORROR / TERROR SFX...")
    for i in range(3):
        write_wav(f"horror_stinger_{i+1}.wav", generate_horror_stinger(random.uniform(1.0, 1.8)))
    for i in range(2):
        write_wav(f"horror_whisper_{i+1}.wav", generate_horror_whisper(random.uniform(1.5, 2.5)))
    for i in range(2):
        write_wav(f"horror_impact_{i+1}.wav", generate_horror_impact(random.uniform(0.6, 1.0)))
    
    print("\n🔮 MYSTERY / SUSPENSE SFX...")
    for i in range(3):
        write_wav(f"mystery_tone_{i+1}.wav", generate_mystery_tone(random.uniform(1.5, 2.5)))
    for i in range(2):
        write_wav(f"suspense_build_{i+1}.wav", generate_suspense_build(random.uniform(2.0, 3.0)))
    
    print("\n⚔️ EPIC / DRAMATIC SFX...")
    for i in range(3):
        write_wav(f"epic_hit_{i+1}.wav", generate_epic_hit(random.uniform(0.8, 1.5)))
    for i in range(2):
        write_wav(f"dramatic_reveal_{i+1}.wav", generate_dramatic_reveal(random.uniform(1.5, 2.0)))
    
    print("\n🔬 CURIOSITY / SCIENCE SFX...")
    for i in range(3):
        write_wav(f"digital_blip_{i+1}.wav", generate_digital_blip(random.uniform(0.3, 0.5)))
    for i in range(2):
        write_wav(f"sci_fi_scan_{i+1}.wav", generate_sci_fi_scan(random.uniform(0.8, 1.2)))
    
    print("\n😢 SAD / EMOTIONAL SFX...")
    for i in range(2):
        write_wav(f"sad_tone_{i+1}.wav", generate_sad_tone(random.uniform(1.5, 2.5)))
    
    print("\n⛈️ NATURE / ENVIRONMENT SFX...")
    for i in range(2):
        write_wav(f"thunder_{i+1}.wav", generate_thunder(random.uniform(1.5, 2.5)))
    
    print("\n✅ All mood-specific SFX generated!")
