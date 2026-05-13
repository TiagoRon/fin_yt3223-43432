from moviepy.editor import VideoFileClip, AudioFileClip, ImageClip, ColorClip, CompositeVideoClip, concatenate_audioclips, concatenate_videoclips, CompositeAudioClip
import moviepy.video.fx.all as vfx
import os
from moviepy.audio.fx.all import audio_loop
import random
import numpy as np
import math
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import textwrap
import re
from src.constants import MUSIC_MOODS, FONT_PATH

# --- VIDEO RESOLUTION ---
# Change these to switch between 720p and 1080p globally
VIDEO_WIDTH = 720
VIDEO_HEIGHT = 1280

# Fix for Pillow 10+ removing ANTIALIAS
if not hasattr(Image, 'ANTIALIAS'):
    Image.ANTIALIAS = Image.LANCZOS

class EffectsManager:
    """
    Manages the visual style ("Vibe") and Effects of the video.
    Ensures mandatory Intro/Outro and varied Middle effects.
    """
    STYLE_HIGH_ENERGY = "high_energy"
    STYLE_SMOOTH = "smooth"
    STYLE_MINIMAL = "minimal"
    
    def __init__(self):
        self.current_style = random.choice([
            self.STYLE_HIGH_ENERGY,
            self.STYLE_SMOOTH,
            self.STYLE_MINIMAL,
            self.STYLE_HIGH_ENERGY # Slight bias towards energy
        ])
        print(f"🎬 VIDEO VIBE: {self.current_style.upper()}")
        
        # Track usage to avoid repetition
        self.used_middle_effects = []
        self.last_effect_time = -10
        
        # RANDOMIZE Intro/Outro for uniqueness — each video gets different combo
        self.intro_effect = random.choice(["cinematic_zoom", "flash_in", "glitch_start", "fade_dramatic"])
        self.outro_effect = random.choice(["glitch_out", "flash_out", "zoom_out_fade"])
        
        print(f"   ✨ Intro: {self.intro_effect} | Outro: {self.outro_effect}")

    def get_zoom_func(self, direction="in", duration=5):
        if direction == "in":
            return lambda t: 1 + 0.04 * (t / duration)
        else: # out
            return lambda t: 1.04 - 0.04 * (t / duration)

    def get_middle_effect(self, current_time, duration):
        """
        Decides if a middle effect should be applied and which one.
        Returns: effect_name or None
        """
        if current_time - self.last_effect_time < 3.0:
            return None
            
        # Probability based on style
        prob = 0.5
        if self.current_style == self.STYLE_HIGH_ENERGY: prob = 0.75
        elif self.current_style == self.STYLE_SMOOTH: prob = 0.45
        elif self.current_style == self.STYLE_MINIMAL: prob = 0.25
        
        if random.random() > prob:
            return None
            
        # EXPANDED pool — 10 effects for maximum variety
        opts = ["glitch_mild", "soft_zoom", "flash", "shake", "pulse", "speed_ramp",
                "color_shift", "whip_pan", "vignette_pulse", "zoom_snap"]
        
        # Don't repeat the last 3 effects
        choices = [o for o in opts if o not in self.used_middle_effects[-3:]]
        if not choices: choices = opts
        
        effect = random.choice(choices)
        self.used_middle_effects.append(effect)
        self.last_effect_time = current_time
        return effect

    def get_transition_prob(self):
        if self.current_style == self.STYLE_HIGH_ENERGY:
            return 0.7 # High chance of transition
        elif self.current_style == self.STYLE_SMOOTH:
            return 0.4
        return 0.1 # Minimal

    def should_glitch(self, duration):
        prob = 0.15
        if self.current_style == self.STYLE_HIGH_ENERGY:
            prob = 0.35
        elif self.current_style == self.STYLE_SMOOTH:
            prob = 0.05
        
        return (random.random() < prob) or (duration > 6.0)

# --- VFX PRIMITIVES ---

def vfx_pulse(clip, duration=0.3):
    """Brief brightness pulse"""
    return clip.fx(vfx.colorx, 1.5).set_duration(duration)

def vfx_slide_in(clip, duration=0.5, direction="left"):
    w, h = clip.size
    if direction == "left":
        return clip.set_position(lambda t: (int(-w + w*(t/duration)), "center") if t < duration else "center")
    return clip

def vfx_zoom_fast(clip, mode="in", duration=0.5):
    if mode == "in":
        return clip.resize(lambda t: 1 + 0.5 * t)
    return clip.resize(lambda t: 1 - 0.5 * t)

def _glitch_frame_impl(im, intensity=25):
    """
    Applies RGB Split glitch to a single frame.
    """
    shift = random.randint(-intensity, intensity)
    if shift == 0: return im
    
    # Roll R and G channels in opposite directions
    r = np.roll(im[:,:,0], shift, axis=1)
    g = np.roll(im[:,:,1], -shift, axis=1)
    b = im[:,:,2]
    return np.stack([r, g, b], axis=2)

def create_flash_transition():
    """Returns a white ColorClip fading out."""
    return ColorClip(size=(VIDEO_WIDTH, VIDEO_HEIGHT), color=(255, 255, 255), duration=0.3).fadeout(0.3)

def vfx_glitch_clip(clip, duration=0.4):
    """
    Takes a clip, slices the first 'duration' seconds, applies glitch, 
    and returns it. 
    """
    if clip.duration < duration:
        duration = clip.duration
    c = clip.subclip(0, duration)
    return c.fl_image(_glitch_frame_impl)

def vfx_shake(clip, strength=5):
    """Simple random shake effect"""
    return clip.set_position(lambda t: (random.randint(-strength, strength), random.randint(-strength, strength)))

def vfx_soft_zoom(clip, duration=None, mode="in"):
    """
    Subtle Ken Burns effect (1.0 -> 1.1).
    Efficient enough for short clips.
    """
    if duration is None: duration = clip.duration
    
    extra_scale = 0.15 # 15% zoom for aggressive cinematic feel
    if mode == "in":
        return clip.resize(lambda t: 1 + extra_scale * (t / max(0.1, duration)))
    else:
        return clip.resize(lambda t: 1 + extra_scale - extra_scale * (t / max(0.1, duration)))

def vfx_slide_transition(clip, start_delay=0, duration=0.5, direction="left"):
    """
    Simulates the clip 'sliding in' from a direction.
    """
    w, h = clip.size
    
    def pos(t):
        if t < start_delay: 
            # Not started yet (effectively invisible if we manage layering right, or just static)
            # Actually for a transition, we usually start at t=0 relative to the clip start
            return "center"
            
        rel_t = t - start_delay
        if rel_t > duration:
            return "center"
        
        progress = rel_t / duration
        # Ease out cubic
        progress = 1 - (1 - progress)**3
        
        if direction == "left": # From Left to Center
            start_x = -w
            return (int(start_x + (0 - start_x)*progress), "center")
        elif direction == "right":
             start_x = w
             return (int(start_x + (0 - start_x)*progress), "center")
        elif direction == "bottom":
             start_y = h
             return ("center", int(start_y + (0 - start_y)*progress))
             
        return "center"

    return clip.set_position(pos)

def vfx_vignette(clip, intensity=0.3):
    """
    Adds a subtle dark vignette to the corners.
    intensity: 0.0 to 1.0 (opacity of the vignette layer)
    """
    # Create a radial gradient mask? MoviePy is slow at this.
    # Alternatives: Just a PNG overlay or a simple color mask.
    # Let's try to perform it using standard composition if possible, 
    # OR simpler: just darken borders?
    
    # Efficient method: 
    # Create an image with radial gradient and overlay it.
    # Since generating it on fly is annoying with PIL every frame, let's make it once.
    w, h = clip.size
    
    # Check if we have a mask cached? No, just create new.
    # For speed, let's assume 1080x1920.
    
    return clip.fx(vfx.margin, 0).fx(vfx.mask_color, color=[0,0,0], thr=0, s=0) 
    # ACTUALLY, simpler approach for "Texture": 
    # Just a very low opacity dark frame
    return clip # Placeholder if too complex for speed.
    
    # Real Vignette implementation using ColorClip + Mask? Too slow.

def vfx_progress_bar(clip, color=(255, 0, 0), height=15):
    """
    Adds a progress bar at the bottom.
    Dynamically generated per frame = Unique frames.
    """
    w, h = clip.size
    d = clip.duration
    
    # We create a ColorClip that moves?
    # Or simpler: A generator clip.
    def make_bar(t):
        if d == 0: progress = 0
        else: progress = t / d
        
        bar_w = int(w * progress)
        # Return a numpy array for the bar?
        # Actually, using ColorClip is easier but requires compositing every frame.
        # Let's use a simpler approach: A static ColorClip of full width, masked by a moving mask?
        # No, moving mask checks duration. 
        return ColorClip(size=(max(1, bar_w), height), color=color).get_frame(t)

    # Efficient way: 
    # Create a full width ColorClip, set a mask that reveals it over time.
    bar = ColorClip(size=(w, height), color=color)
    bar = bar.set_duration(d) # CRITICAL FIX: Set duration!
    
    # Mask: Moving white rectangle.
    # It's faster to just use a custom clip generation function if we wanted, 
    # but MoviePy composition is easier.
    
    # Let's use a dynamic position approach.
    # 1. Start with bar at x = -w
    # 2. Move to x = 0
    # No, that slides it. We want stretch.
    
    # Resize approach (easiest for GPU/CPU):
    # Take a 1xHeight pixel bar, resize its Width over time.
    # But resize is slow per frame.
    
    # Let's try the Sliding Bar approach: simpler and looks cool.
    # Bar starts fully off-screen left, slides in.
    bar = bar.set_position(lambda t: (int(-w + w*(t/d)), h - height))
    
    # CRITICAL: Ensure composite has duration
    return CompositeVideoClip([clip, bar], size=(w,h)).set_duration(d)

def vfx_grain(clip, intensity=0.05):
    """
    Adds film grain noise overlay. 
    Using a static noise image looped is faster than generating per frame.
    """
    # Just return clip if noise is too heavy.
    # We will simulate "Noise" by just adding a static overlay with very low opacity
    # that jitters position slightly.
    return clip # Placeholder for now to avoid rendering crash.
    # Grain is heavy.


def vfx_color_grade(clip, preset="cinematic"):
    """
    Applies a color grade to make the video look more produced.
    Standard 'Cinematic' = slight contrast boost + saturation helper + tiny warm tint.
    """
    # Softer contrast boost (0.08) to prevent blowing out stock footage
    # Use color filter for cinematic look (slightly dark/warm feel via RGB multiplier)
    c = clip.fx(vfx.lum_contrast, lum=0, contrast=0.10, contrast_thr=127)
    return c.fx(vfx.colorx, 0.95) # Slight darkening for professional tone

def vfx_mirror(clip):
    """
    Horizontally flips the video. 
    Strong signature change for avoiding 'Reused Content'.
    """
    return clip.fx(vfx.mirror_x)

def create_title_card(text, duration=2.5, width=VIDEO_WIDTH, height=VIDEO_HEIGHT):
    """
    Creates a 'Cuadradito' style title badge.
    Deep Yellow/Orange background box, Black text. 
    Appears centered. Auto-scales font for long titles.
    """
    if not text: return None
    
    # Auto-scale font based on text length
    text_len = len(text)
    if text_len <= 25:
        fontsize = 60
        wrap_width = 16
    elif text_len <= 45:
        fontsize = 48
        wrap_width = 20
    elif text_len <= 70:
        fontsize = 38
        wrap_width = 26
    else:
        fontsize = 32
        wrap_width = 32
    
    # Font Setup
    font_path = FONT_PATH
    try:
        font = ImageFont.truetype(font_path, fontsize)
    except IOError:
        try:
            possible_fonts = [f for f in os.listdir("assets/fonts") if f.endswith(".ttf")]
            if possible_fonts:
                fallback = os.path.join("assets/fonts", possible_fonts[0])
                font = ImageFont.truetype(fallback, fontsize)
            else:
                font = ImageFont.load_default()
        except:
            font = ImageFont.load_default()
        
    # Wrap text — limit to 4 lines max to keep it clean
    lines = textwrap.wrap(text, width=wrap_width)
    if len(lines) > 4:
        lines = lines[:4]
        lines[-1] = lines[-1][:len(lines[-1])-3] + "..."
    
    # Measure Text
    img_temp = Image.new('RGBA', (1, 1))
    draw_temp = ImageDraw.Draw(img_temp)
    
    line_metrics = []
    max_w = 0
    total_text_h = 0
    
    for line in lines:
        bbox = draw_temp.textbbox((0, 0), line, font=font)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        max_w = max(max_w, w)
        line_metrics.append((w, h))
        total_text_h += h + 15
    
    total_text_h -= 15
    
    # Box Dimensions (Padding)
    pad_x = 40
    pad_y = 30
    box_w = min(max_w + (pad_x * 2), width - 60)  # Don't exceed screen width
    box_h = total_text_h + (pad_y * 2)
    
    # Draw Final Image
    img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Center Box
    box_x1 = (width - box_w) // 2
    box_y1 = (height - box_h) // 2
    box_x2 = box_x1 + box_w
    box_y2 = box_y1 + box_h
    
    # Draw "Cuadradito" (Yellow/Gold Background)
    draw.rectangle([box_x1, box_y1, box_x2, box_y2], fill="#FFC107", outline="white", width=4)
    
    # Draw Text
    curr_y = box_y1 + pad_y
    for i, line in enumerate(lines):
        w, h = line_metrics[i]
        line_x = box_x1 + (box_w - w) // 2
        
        # Black Text
        draw.text((line_x, curr_y), line, font=font, fill="black")
        curr_y += h + 15
        
    # Clip
    clip = ImageClip(np.array(img)).set_duration(duration).set_position(("center", int(height * 0.27)))
    
    # Animation: Pop in
    clip = clip.resize(lambda t: min(1, 0.8 + 2*t) if t < 0.1 else 1)
    
    return clip

def create_karaoke_clips(word_timings, duration, start_offset, width=VIDEO_WIDTH, height=VIDEO_HEIGHT, fontsize=75, raw_text="", is_header=False):
    import re
    # Professional Shorts Style: Single Line Focused
    if is_header:
        fontsize = 60 # Slightly smaller to fit box
    else:
        fontsize = 75 # Bigger
    
    # Load Font - Custom Branding
    font_path = FONT_PATH
    font = None
    
    print(f"   🔎 Debug Font Path: {os.path.abspath(font_path)}")
    if os.path.exists(font_path):
        print("      ✅ Font file exists at path.")
    else:
        print("      ❌ Font file NOT FOUND at path.")
        
    try:
        font = ImageFont.truetype(font_path, fontsize)
        print(f"      ✅ Loaded Custom Font: {font_path}")
    except IOError as e:
        print(f"      ⚠️ Failed to load custom font {font_path}: {e}")
        # Fallback: Try to find any .ttf in assets
        try:
            possible_fonts = [f for f in os.listdir("assets/fonts") if f.endswith(".ttf")]
            if possible_fonts:
                fallback = os.path.join("assets/fonts", possible_fonts[0])
                print(f"      🔄 Retrying with fallback: {fallback}")
                font = ImageFont.truetype(fallback, fontsize)
            else:
                print("      ❌ No fallback fonts found in assets/fonts.")
                font = ImageFont.load_default()
        except Exception as ex:
            print(f"      ❌ Fallback failed: {ex}")
            font = ImageFont.load_default()

    # Pre-calculate Layout (Map words to lines)
    if is_header:
        # Match subtitles punchy style
        chars_per_line = 12
    else:
        # If fallback to default font (PIL default is tiny), we need huge adjustments or it will be unreadable.
        # But load_default() returns a font object that might behave differently.
        # Let's verify what font object we have.
        if isinstance(font, ImageFont.FreeTypeFont): # Changed from ImageFont.ImageFont to ImageFont.FreeTypeFont for accuracy
             # TrueType
             # INCREASED ESTIMATE: Montserrat ExtraBold is WIDE. 0.50 was too optimistic.
             avg_char_width = fontsize * 0.65 
        else:
             # Default (Bitmap?)
             avg_char_width = 10 # Tiny
             
        # Use narrower width to force 2-4 words per line (Punchy style)
        # Reduced multiplier from 0.7 to 0.6 to give more safety margin
        chars_per_line = int((width * 0.6) / avg_char_width) 
    
    # Prepare full_text
    full_text = raw_text if raw_text else ""
    full_text = re.sub(r'[^\w\s\.,!?\'"()\-:;áéíóúÁÉÍÓÚñÑüÜ¿¡&$+=\\/%]', '', full_text)
    
    if not full_text and not word_timings:
        return []

    # --- CRITICAL FIX: Sanitize Timings to match Visual Tokens ---
    # Issue: TTS might return "New York" as 1 item, but textwrap splits it into 2.
    # Result: Desync.
    # Solution: Flatten timings so 1 timing entry = 1 visual word.
    
    sanitized_timings = []
    if word_timings:
        for w_data in word_timings:
            # 1. Strip whitespace
            raw_w = w_data.get('word', '').strip()
            # Clean Emojis to prevent empty square boxes in output
            raw_w = re.sub(r'[^\w\s\.,!?\'"()\-:;áéíóúÁÉÍÓÚñÑüÜ¿¡&$+=\\/%]', '', raw_w)
            if not raw_w: continue # Skip empty/silence
            
            # 2. Check for internal spaces
            sub_words = raw_w.split()
            if len(sub_words) == 1:
                sanitized_timings.append({
                    'word': raw_w,
                    'start': w_data['start'],
                    'end': w_data['end']
                })
            else:
                # Split duration among sub-words
                total_dur = w_data['end'] - w_data['start']
                char_counts = [len(sw) for sw in sub_words]
                total_chars = sum(char_counts)
                
                curr_start = w_data['start']
                for sw, chars in zip(sub_words, char_counts):
                    # Proportional duration
                    portion = chars / total_chars if total_chars > 0 else 1/len(sub_words)
                    sw_dur = total_dur * portion
                    
                    sanitized_timings.append({
                        'word': sw,
                        'start': curr_start,
                        'end': curr_start + sw_dur
                    })
                    curr_start += sw_dur
    
    word_timings = sanitized_timings # Replace with clean list
    
    # Re-generate full_text strictly from sanitized list to ensure 100% match
    full_text = " ".join([w['word'] for w in word_timings])

    # 1. Break text into logical clauses based on punctuation
    # This ensures lines don't break unnaturally across sentences
    clauses = re.split(r'(?<=[.!?])\s+', full_text)
    
    wrap_width = 25 if is_header else max(15, chars_per_line)
    lines_strings = []
    
    for clause in clauses:
        if not clause.strip(): continue
        # 2. Wraps the clause if it's longer than wrap_width
        wrapped = textwrap.wrap(clause, width=wrap_width, break_long_words=False)
        lines_strings.extend(wrapped)
        
    # Map global word index to (line_index, word_in_line_index, line_string)
    word_map = {} 
    
    global_w_idx = 0
    parsed_lines = []
    
    for l_idx, line_str in enumerate(lines_strings):
        l_words = line_str.split()
        parsed_lines.append(l_words)
        for w_in_l_idx, w_str in enumerate(l_words):
             word_map[global_w_idx] = {
                 "line_idx": l_idx,
                 "word_idx_in_line": w_in_l_idx,
                 "line_words": l_words
             }
             global_w_idx += 1
    
    # Pre-calculate optimal font size per line to prevent clipping
    # Map: line_idx -> (font_object)
    line_font_map = {}
    
    # Init temp drawer for measurement
    img_temp = Image.new('RGBA', (1, 1))
    draw_temp = ImageDraw.Draw(img_temp)
    
    for l_idx, line_str in enumerate(lines_strings):
        # Start with default size
        curr_fontsize = fontsize
        while True:
            try:
                if "impact" in font_path.lower():
                     tmp_font = ImageFont.truetype(font_path, curr_fontsize)
                else:
                     tmp_font = ImageFont.truetype(font_path, curr_fontsize)
            except:
                tmp_font = ImageFont.load_default()
                break
                
            # Measure
            bbox = draw_temp.textbbox((0, 0), line_str, font=tmp_font)
            line_w = bbox[2] - bbox[0]
            
            # Allow smaller font (down to 20px) and check against safe width (width - 100)
            if line_w <= (width - 100) or curr_fontsize <= 20:
                line_font_map[l_idx] = tmp_font
                if curr_fontsize < fontsize:
                     print(f"      🔧 Resizing line '{line_str[:15]}...' to {curr_fontsize}px (Width: {line_w})")
                break
            
            # Reduce and retry
            curr_fontsize -= 5
            
    # Colors
    if is_header:
        active_color = "white" # Pops cleanly inside yellow
        default_color = "black" 
        box_color = "#FFC107" # Smooth Yellow
        box_border = "black" 
        stroke_width = 5 
        stroke_color = "black"
        shadow_offset = (5, 5)
        shadow_color = "black"
    else:
        active_color = "#FFD700" # Gold
        default_color = "white"
        stroke_color = "black"
        stroke_width = 5 
        shadow_offset = (5, 5)
        shadow_color = "black"

    # --- OPTIMIZATION: Generate Single Concatenated Track ---
    # 1. Resolve Overlaps & Gaps
    final_timings = []
    prev_end = 0
    
    for i in range(len(word_timings)):
        w = word_timings[i]
        start = w['start'] + start_offset
        end = w['end'] + start_offset
        
        if start < prev_end:
            start = prev_end # Avoid overlap back-shifting
        if end <= start: 
            end = start + 0.1 
            
        # MAGNETIC GAPS: Close very small gaps between words to prevent flashing
        if i > 0 and start > prev_end:
            gap_dur = start - prev_end
            if gap_dur < 2.0: # Keep text on screen during natural pauses (up to 2s)
                final_timings[-1]['end'] = start
                final_timings[-1]['duration'] = final_timings[-1]['end'] - final_timings[-1]['start']
                prev_end = start
        
        gap = start - prev_end
        if gap < 0: gap = 0 
        
        final_timings.append({
            'word': w['word'],
            'start': start,
            'end': end,
            'duration': end - start,
            'gap_before': gap,
            'original_idx': i
        })
        prev_end = end

    # 2. Build Clip Sequence
    clips_sequence = []
            
    for ft in final_timings:
        if ft['gap_before'] > 0.001:
            clips_sequence.append(ColorClip(size=(width, height), color=(0,0,0,0), duration=ft['gap_before']))
            
        orig_i = ft['original_idx']
        
        if orig_i not in word_map: continue
        
        mapping = word_map[orig_i]
        current_line_words = mapping["line_words"]
        l_idx = mapping["line_idx"]
        active_word_in_line = mapping["word_idx_in_line"]
        
        line_font = line_font_map.get(l_idx, font)
        
        img_base = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw_base = ImageDraw.Draw(img_base)
        
        full_line_lbl = " ".join(current_line_words)
        bbox = draw_base.textbbox((0, 0), full_line_lbl, font=line_font)
        line_w = 0
        line_h = bbox[3] - bbox[1]
        for w_idx, w_txt in enumerate(current_line_words):
             w_bbox = draw_base.textbbox((0, 0), w_txt, font=line_font)
             line_w += (w_bbox[2] - w_bbox[0])
             if w_idx < len(current_line_words) - 1:
                 line_w += draw_base.textlength(" ", font=line_font)
        line_w = int(line_w)
        
        if is_header:
            start_y = int(height * 0.27)
        else:
            start_y = (height - line_h) // 2
            
        current_x = (width - line_w) // 2
        
        # Draw Aesthetic Yellow Box for Header
        if is_header:
             pad = 40 
             bbox_full = draw_base.textbbox((current_x, start_y), full_line_lbl, font=line_font)
             true_top = bbox_full[1]
             true_bottom = bbox_full[3]
             draw_base.rounded_rectangle(
                 [current_x - pad, true_top - pad, current_x + line_w + pad, true_bottom + pad],
                 radius=20, fill=box_color, outline=box_border, width=5
             )
        
        active_word_x = 0
        active_word_y = start_y
        active_word_txt = ""
             
        for w_idx, w_txt in enumerate(current_line_words):
             if w_idx == active_word_in_line:
                 active_word_x = current_x
                 active_word_txt = w_txt
             else:
                 fill = default_color
                 if stroke_width > 0 and not is_header:
                     for angle in range(0, 360, 15):
                         rad = math.radians(angle)
                         dx = int(math.cos(rad) * stroke_width)
                         dy = int(math.sin(rad) * stroke_width)
                         draw_base.text((current_x + dx, start_y + dy), w_txt, font=line_font, fill=stroke_color)
                     draw_base.text((current_x + shadow_offset[0], start_y + shadow_offset[1]), w_txt, font=line_font, fill=shadow_color)
                 draw_base.text((current_x, start_y), w_txt, font=line_font, fill=fill)
             
             w_bbox = draw_base.textbbox((0, 0), w_txt, font=line_font)
             w_w = w_bbox[2] - w_bbox[0]
             space_w = draw_base.textlength(" ", font=line_font)
             current_x += w_w + space_w
             
        base_clip = ImageClip(np.array(img_base)).set_duration(ft['duration'])
        
        if active_word_txt:
            a_bbox = draw_base.textbbox((0, 0), active_word_txt, font=line_font)
            pad = 50 
            a_w = int(a_bbox[2] - a_bbox[0]) + (stroke_width*2) + pad*2 
            a_h = int(a_bbox[3] - a_bbox[1]) + (stroke_width*2) + shadow_offset[1] + pad*2
            
            img_active = Image.new('RGBA', (a_w, a_h), (0, 0, 0, 0))
            draw_active = ImageDraw.Draw(img_active)
            
            local_x = pad - a_bbox[0]
            local_y = pad - a_bbox[1]
            
            if stroke_width > 0 and not is_header:
                 for angle in range(0, 360, 15):
                     rad = math.radians(angle)
                     dx = int(math.cos(rad) * stroke_width)
                     dy = int(math.sin(rad) * stroke_width)
                     draw_active.text((local_x + dx, local_y + dy), active_word_txt, font=line_font, fill=stroke_color)
                 draw_active.text((local_x + shadow_offset[0], local_y + shadow_offset[1]), active_word_txt, font=line_font, fill=shadow_color)
            
            draw_active.text((local_x, local_y), active_word_txt, font=line_font, fill=active_color)
            
            active_clip = ImageClip(np.array(img_active)).set_duration(ft['duration'])
            
            word_dur = ft['duration']
            def pop_scale(t):
                progress = min(1.0, t / word_dur)
                bounce = math.sin(progress * math.pi)
                # INCREASED BOUNCE FACTOR for punchier text (from 0.12 to 0.25)
                return 1.0 + (0.25 * bounce) 
                
            active_clip = active_clip.resize(pop_scale)
            comp_x = active_word_x - local_x
            comp_y = active_word_y - local_y
            txt_clip = CompositeVideoClip([base_clip, active_clip.set_position((comp_x, comp_y))])
        else:
            txt_clip = base_clip
            
        clips_sequence.append(txt_clip)
        
    if not clips_sequence: return []
    
    # --- STATIC TAIL FOR HEADERS ---
    if is_header and duration > final_timings[-1]['end']:
        tail_dur = duration - final_timings[-1]['end']
        if tail_dur > 0.1:
            # We must redraw the last line completely in default colors so the last word doesn't vanish
            mapping = word_map[final_timings[-1]['original_idx']]
            last_line_words = mapping["line_words"]
            l_idx = mapping["line_idx"]
            line_font = line_font_map.get(l_idx, font)
            
            img_tail = Image.new('RGBA', (width, height), (0, 0, 0, 0))
            draw_tail = ImageDraw.Draw(img_tail)
            
            full_line_lbl = " ".join(last_line_words)
            bbox = draw_tail.textbbox((0, 0), full_line_lbl, font=line_font)
            line_w = 0
            for w_idx, w_txt in enumerate(last_line_words):
                 w_bbox = draw_tail.textbbox((0, 0), w_txt, font=line_font)
                 line_w += (w_bbox[2] - w_bbox[0])
                 if w_idx < len(last_line_words) - 1:
                     line_w += draw_tail.textlength(" ", font=line_font)
            line_w = int(line_w)
            
            start_y = int(height * 0.27)
            current_x = (width - line_w) // 2
            
            # Draw aesthetic yellow box for tail
            pad = 40 
            bbox_full = draw_tail.textbbox((current_x, start_y), full_line_lbl, font=line_font)
            true_top = bbox_full[1]
            true_bottom = bbox_full[3]
            draw_tail.rounded_rectangle(
                [current_x - pad, true_top - pad, current_x + line_w + pad, true_bottom + pad],
                radius=20, fill=box_color, outline=box_border, width=5
            )
            
            # Draw all words in default color for the tail
            for w_txt in last_line_words:
                 draw_tail.text((current_x, start_y), w_txt, font=line_font, fill=default_color)
                 w_bbox = draw_tail.textbbox((0, 0), w_txt, font=line_font)
                 w_w = w_bbox[2] - w_bbox[0]
                 space_w = draw_tail.textlength(" ", font=line_font)
                 current_x += w_w + space_w
                 
            base_tail = ImageClip(np.array(img_tail)).set_duration(tail_dur)
            clips_sequence.append(base_tail)
            
    # Concatenate to single track
    # Use chain because all are same size (width, height)
    final_track = concatenate_videoclips(clips_sequence, method="chain")
    final_track = final_track.set_position("center") # Ensure position
    
    return [final_track] # Return as list to be compatible with 'extend'


def create_short(script_data, audio_files, background_dir, music_dir, output_file):
    try:
        # Load Audio
        audio_clips = [AudioFileClip(f) for f in audio_files]
        full_audio = concatenate_audioclips(audio_clips)
        total_duration = full_audio.duration

        # Background
        bg_files = [f for f in os.listdir(background_dir) if f.endswith(('.mp4', '.mov'))]
        if not bg_files:
             raise FileNotFoundError(f"No background videos found in {background_dir}")
        bg_path = os.path.join(background_dir, random.choice(bg_files))
        video_bg = VideoFileClip(bg_path)
        
        # ... logic continues ...
        # Use context manager or explicit close for video_bg later

        
        if video_bg.duration < total_duration:
            video_bg = video_bg.loop(duration=total_duration + 1.5)
            
        # Crop 9:16
        target_ratio = 9/16
        if video_bg.w / video_bg.h > target_ratio:
            new_w = int(video_bg.h * target_ratio)
            video_bg = video_bg.crop(x1=video_bg.w/2 - new_w/2, width=new_w, height=video_bg.h)
            
        video_bg = video_bg.resize(height=VIDEO_HEIGHT)
        video_bg = video_bg.subclip(0, total_duration)

        # Slow Zoom (Ken Burns) - REMOVED for Performance (Causes 30min+ render times)
        # video_bg = video_bg.resize(lambda t: 1 + 0.02 * t) 
        
        # Dynamic Karaoke Subtitles
        subtitle_clips = []
        current_time = 0
        texts = [script_data['hook'], script_data['body'], script_data['climax']]
        
        for i, audioclip in enumerate(audio_clips):
            txt = texts[i]
            dur = audioclip.duration
            word_clips = create_karaoke_clips(txt, dur, current_time, width=VIDEO_WIDTH, height=VIDEO_HEIGHT)
            subtitle_clips.extend(word_clips)
            current_time += dur

        # Music
        final_audio = full_audio
        if os.path.isdir(music_dir):
            m_files = [f for f in os.listdir(music_dir) if f.endswith('.mp3')]
            if m_files:
                music = AudioFileClip(os.path.join(music_dir, random.choice(m_files)))
                if music.duration < total_duration:
                    music = music.loop(duration=total_duration)
                else:
                    music = music.subclip(0, total_duration)
                final_audio = CompositeAudioClip([full_audio, music.volumex(0.15)])

        final_layers = [video_bg] + subtitle_clips
        final = CompositeVideoClip(final_layers, size=(VIDEO_WIDTH, VIDEO_HEIGHT)).set_audio(final_audio)
        final.write_videofile(output_file, fps=30, codec='libx264', audio_codec='aac', bitrate="5000k", preset='fast', threads=4)
        
        # Cleanup
        final.close()
        for c in final_clips:
            try: c.close()
            except: pass
        for sfx in sfx_lib.values():
            try: sfx.close()
            except: pass
            
        return True

    except Exception as e:
        print(f"Error creating visual comp: {e}")
        return False

def assemble_video(scenes, music_dir, output_file, title_text=None, mood="mystery", watermark_text="", is_cancelled=None, progress_callback=None):
    """
    Assembles the final video from a list of processed scenes.
    OPTIMIZED FOR SPEED: Uses threads, faster preset, and early resizing.
    """
    try:
        if not scenes:
            print("❌ No scenes provided to assemble_video. Aborting.")
            return False
            
        final_clips = []
        
        # Initialize Style
        style_mgr = EffectsManager()
        
        # --- LOAD SFX LIBRARY ---
        _project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        sfx_dir = os.path.join(_project_root, "sfx")
        sfx_lib = {}
        if os.path.exists(sfx_dir):
            for f in os.listdir(sfx_dir):
                name = os.path.splitext(f)[0].lower()
                if not (f.endswith('.wav') or f.endswith('.mp3')): continue
                try:
                    clip = AudioFileClip(os.path.join(sfx_dir, f))
                    # Store at FULL volume — volume control happens where SFX are applied
                    sfx_lib[name] = clip
                except Exception as ex:
                    print(f"Failed to load SFX {f}: {ex}")
            print(f"SFX Library loaded: {len(sfx_lib)} effects from {sfx_dir}")
        else:
            print(f"WARNING: SFX directory not found at {sfx_dir}")

        # Helper to get random SFX by type
        def get_sfx(kind):
            # Extended SFX library: all types are now available but at subtle volumes
            matches = [k for k in sfx_lib.keys() if kind in k]
            if matches:
                # Prefer generated ones if available for variety
                gen_matches = [m for m in matches if '_gen_' in m]
                if gen_matches and random.random() < 0.7:
                     return sfx_lib[random.choice(gen_matches)]
                return sfx_lib[random.choice(matches)]
            return None
        
        for idx, scene in enumerate(scenes):
            # Load assets
            audio_path = scene.get('audio_path')
            if not audio_path: continue
                
            video_paths = scene.get('video_paths', [scene.get('video_path')]) 
            timings = scene.get('timings', [])
            text = scene.get('text', "")
            
            audioclip = AudioFileClip(audio_path)
            duration = audioclip.duration
            
            # --- VISUAL ASSEMBLY --
            num_v_clips = len(video_paths)
            clip_duration_target = duration / max(1, num_v_clips)
            
            scene_v_clips = []
            for i, vp in enumerate(video_paths):
                if not vp or not os.path.exists(vp): continue
                
                # Check for tiny/corrupted files (< 10KB)
                if os.path.getsize(vp) < 10000:
                    print(f"      ⚠️ Skipping suspect file (too small): {vp}")
                    continue

                # Check extensions
                ext = os.path.splitext(vp)[1].lower()
                is_image = ext in ['.jpg', '.jpeg', '.png', '.webp']
                
                if is_image:
                     # KEN BURNS IMAGE (Static Photo -> Fake Dynamic Video)
                     try:
                         # Load image as RGB (prevents alpha/broadcast NumPy crash)
                         pil_img = Image.open(vp).convert('RGB')
                         src_w, src_h = pil_img.size
                         target_ratio = VIDEO_WIDTH / VIDEO_HEIGHT
                         src_ratio = src_w / src_h
                         
                         # PRE-SCALE WITH EXTRA MARGIN: ensure zoomed image is always
                         # larger than canvas so Ken Burns NEVER reveals black edges.
                         # Scale so the shortest axis covers 130% of canvas.
                         margin = 1.30
                         if src_ratio > target_ratio:
                             # Wider: scale by height
                             scale = (VIDEO_HEIGHT * margin) / src_h
                         else:
                             # Taller: scale by width
                             scale = (VIDEO_WIDTH * margin) / src_w
                         
                         new_w = max(VIDEO_WIDTH + 2, int(src_w * scale))
                         new_h = max(VIDEO_HEIGHT + 2, int(src_h * scale))
                         pil_img = pil_img.resize((new_w, new_h), Image.LANCZOS)
                         
                         img = ImageClip(np.array(pil_img))
                         needed_dur = clip_duration_target + 0.5
                         img = img.set_duration(needed_dur)
                         
                         # Gentle Ken Burns zoom on the pre-scaled image (8% total)
                         zoom_mode = random.choice(["in", "out"])
                         kb_scale = 0.08
                         if zoom_mode == "in":
                             img = img.resize(lambda t: 1 + kb_scale * (t / max(0.1, needed_dur)))
                         else:
                             img = img.resize(lambda t: 1 + kb_scale - kb_scale * (t / max(0.1, needed_dur)))
                         
                         # Hard center-crop to EXACT canvas — this eliminates ALL black bars
                         # regardless of what happens during zoom
                         img = img.crop(x_center=img.w / 2, y_center=img.h / 2,
                                        width=VIDEO_WIDTH, height=VIDEO_HEIGHT)
                         
                         c = img
                         print(f"      📸 Image→Clip (Ken Burns, sin barras): {os.path.basename(vp)}")
                         
                     except Exception as e_img:
                         print(f"      ⚠️ Failed to load image clip {vp}: {e_img}")
                         continue
                else:
                    # VIDEO CLIP
                    try:
                        c = VideoFileClip(vp)
                        # ROBUSTNESS CHECK: Try to read a frame to ensure file is valid
                        c.get_frame(0)
                    except Exception as e:
                        print(f"      ⚠️ Failed to load clip {vp} (Corrupt?): {e}")
                        if 'c' in locals(): 
                            try: c.close()
                            except: pass
                        continue
                    
                    # 9:16 Crop/Fill - OPTIMIZED: Resize immediately to avoid processing 4k
                    target_ratio = VIDEO_WIDTH / VIDEO_HEIGHT
                    
                    if c.w != VIDEO_WIDTH or c.h != VIDEO_HEIGHT:
                        # Only resize if needed (Logic for dynamic resize/crop)
                        # If much larger, resize first close to target height (Optimization)
                        if c.h > 2000:
                            c = c.resize(height=VIDEO_HEIGHT) 
                            # Force GC after heavy resize
                            import gc
                            gc.collect() 
                        
                        # OPTIMIZATION: Always use Center Crop (Fill) for standard 16:9 content.
                        # The previous "Blurry Background" effect (Composite 2 layers) was doubling the render time per frame.
                        # For stock footage (atmosphere, people), Center Crop is standard for Shorts.
                        
                        w, h = c.size
                        input_ratio = w / float(h)
                        target_ratio = VIDEO_WIDTH / float(VIDEO_HEIGHT)
                         
                        if input_ratio > target_ratio:
                            # Input is "wider" than target (e.g. 16:9 vs 9:16) -> Fill Height, Crop Sides
                            new_w = int(w * (float(VIDEO_HEIGHT) / h) + 2) # Adding 2px buffer to prevent float cutoff
                            c = c.resize(newsize=(new_w, VIDEO_HEIGHT))
                            c = c.crop(x_center=c.w/2, width=VIDEO_WIDTH, height=VIDEO_HEIGHT)
                        else:
                            # Input is "taller" than target (rare/skinny) -> Fill Width, Crop Top/Bottom
                            new_h = int(h * (float(VIDEO_WIDTH) / w) + 2)
                            c = c.resize(newsize=(VIDEO_WIDTH, new_h))
                            c = c.crop(y_center=c.h/2, width=VIDEO_WIDTH, height=VIDEO_HEIGHT)
                
                # --- NEW ORIGINALITY FILTERS ---
                # 1. Color Grading (Cinematic Style)
                c = vfx_color_grade(c)
                
                # 2. Random Mirroring (50% chance) - Only for videos? Images can mirror too.
                if random.random() < 0.5:
                    c = vfx_mirror(c)

                # Duration Loop
                needed_dur = clip_duration_target + 0.5 
                if c.duration < needed_dur: c = c.loop(duration=needed_dur)
                else: c = c.subclip(0, needed_dur)

                # --- APPLY FAST PACING (STATIC PUNCH ZOOMS + CONSTANT MOTION) ---
                # Apply dynamic movement on EVERY clip for constant flow
                if not is_image:
                    zoom_dir = random.choice(["in", "out"])
                    c = vfx_soft_zoom(c, duration=needed_dur, mode=zoom_dir)
                    # Re-lock to canvas after zoom
                    c = CompositeVideoClip([c.set_position(lambda t: ('center', 'center'))], size=(VIDEO_WIDTH, VIDEO_HEIGHT)).set_duration(needed_dur)
                # Images already have Ken Burns applied during clip creation — skip second zoom pass
                # (extra zoom on a pre-cropped image causes black edges)
                
                # Static punch zoom variation on top of slow zoom
                zoom_factor = 1.0
                if i % 3 == 1:
                    zoom_factor = 1.25  # Punch in 25% (was 15%)
                elif i % 3 == 2:
                    zoom_factor = 1.15  # Micro punch 15% (was 8%)
                
                if zoom_factor > 1.0:
                    c = c.resize(zoom_factor)
                    c = c.crop(x_center=c.w/2, y_center=c.h/2, width=VIDEO_WIDTH, height=VIDEO_HEIGHT)
                
                scene_v_clips.append(c)
                
            if not scene_v_clips: continue 
                
            # Combine Visuals
            if len(scene_v_clips) > 1:
                print(f"      🔗 Concatenating {len(scene_v_clips)} clips for scene {idx}...")
                full_visual = concatenate_videoclips(scene_v_clips, method="compose", padding=-0.25)
            else:
                full_visual = scene_v_clips[0]
            
            if full_visual.duration < duration:
                full_visual = full_visual.loop(duration=duration)
            full_visual = full_visual.subclip(0, duration)
            
            # --- APPLY MIDDLE EFFECTS ---
            # Current timeframe validation
            # We approximate current_time based on previously added clips
            # (In a real scenario we'd track total duration, here we trust the manager logic purely on sequence)
            
            # Note: For accurate time tracking we'd need to sum durations, but simple sequence logic works for "variety"
            effect_type = style_mgr.get_middle_effect(idx * 3.0, duration) # Approximate time
            effect_applied = False
            
            if effect_type:
                if effect_type == "glitch_mild":
                    glitched_part = vfx_glitch_clip(full_visual, duration=0.4)
                    full_visual = CompositeVideoClip([full_visual, glitched_part.set_start(0)], size=(VIDEO_WIDTH,VIDEO_HEIGHT))
                    sfx = get_sfx('glitch_gen') or get_sfx('glitch')
                    if sfx: audioclip = CompositeAudioClip([audioclip, sfx.set_start(0).volumex(0.20)])
                    effect_applied = True
                    
                elif effect_type == "shake":
                    full_visual = vfx_shake(full_visual, strength=8)
                    sfx = get_sfx('swoosh')
                    if sfx: audioclip = CompositeAudioClip([audioclip, sfx.set_start(0).volumex(0.18)])
                    effect_applied = True

                elif effect_type == "pulse":
                    pulse = full_visual.subclip(0, 0.3).fx(vfx.colorx, 1.4)
                    rest = full_visual.subclip(0.3)
                    full_visual = concatenate_videoclips([pulse, rest])
                    sfx = get_sfx('bass_drop') or get_sfx('epic_hit') or get_sfx('boom')
                    if sfx: audioclip = CompositeAudioClip([audioclip, sfx.set_start(0).volumex(0.20)])
                    effect_applied = True
                    
                elif effect_type == "soft_zoom":
                     full_visual = vfx_soft_zoom(full_visual, duration=duration, mode=random.choice(["in", "out"]))
                     # Subtle shimmer on zoom
                     sfx = get_sfx('shimmer')
                     if sfx: audioclip = CompositeAudioClip([audioclip, sfx.set_start(0.2).volumex(0.12)])
                     effect_applied = True
                     
                elif effect_type == "flash":
                     flash = create_flash_transition()
                     full_visual = CompositeVideoClip([full_visual, flash.set_start(0)], size=(VIDEO_WIDTH,VIDEO_HEIGHT))
                     sfx = get_sfx('shimmer') or get_sfx('dramatic_reveal')
                     if sfx: audioclip = CompositeAudioClip([audioclip, sfx.set_start(0).volumex(0.18)])
                     effect_applied = True
                
                elif effect_type == "speed_ramp":
                    try:
                        mid = duration / 2
                        first_half = full_visual.subclip(0, mid).fx(vfx.speedx, 1.15)
                        second_half = full_visual.subclip(mid).fx(vfx.speedx, 0.8)
                        full_visual = concatenate_videoclips([first_half, second_half])
                        if full_visual.duration < duration:
                            full_visual = full_visual.loop(duration=duration)
                        full_visual = full_visual.subclip(0, duration)
                        # Swoosh on speed change
                        sfx = get_sfx('swoosh')
                        if sfx: audioclip = CompositeAudioClip([audioclip, sfx.set_start(mid*0.85).volumex(0.15)])
                        effect_applied = True
                    except:
                        pass
                
                # --- NEW EFFECTS V4 ---
                elif effect_type == "color_shift":
                    # Tint the scene briefly (cinematic color wash)
                    try:
                        tint_dur = min(0.5, duration * 0.15)
                        tinted = full_visual.subclip(0, tint_dur).fx(vfx.colorx, 0.7)  # Darken briefly
                        rest = full_visual.subclip(tint_dur)
                        full_visual = concatenate_videoclips([tinted, rest])
                        sfx = get_sfx('mystery_tone') or get_sfx('suspense_build')
                        if sfx: audioclip = CompositeAudioClip([audioclip, sfx.set_start(0).volumex(0.18)])
                        effect_applied = True
                    except:
                        pass
                
                elif effect_type == "whip_pan":
                    # Quick horizontal blur/slide effect  
                    try:
                        blur_dur = 0.15
                        # Create motion blur by offsetting frames
                        blur_clip = full_visual.subclip(0, blur_dur).resize(lambda t: 1 + 2*t/blur_dur if t < blur_dur/2 else 3 - 2*t/blur_dur)
                        rest = full_visual.subclip(blur_dur)
                        full_visual = concatenate_videoclips([blur_clip, rest])
                        sfx = get_sfx('swoosh')
                        if sfx: audioclip = CompositeAudioClip([audioclip, sfx.set_start(0).volumex(0.22)])
                        effect_applied = True
                    except:
                        pass
                        
                elif effect_type == "vignette_pulse":
                    # Dark edges pulse in and out
                    try:
                        vignette_dur = min(0.4, duration * 0.1)
                        dark_frame = full_visual.subclip(0, vignette_dur).fx(vfx.colorx, 0.5)
                        rest = full_visual.subclip(vignette_dur)
                        full_visual = concatenate_videoclips([dark_frame, rest])
                        sfx = get_sfx('bass_drop') or get_sfx('horror_impact') or get_sfx('boom')
                        if sfx: audioclip = CompositeAudioClip([audioclip, sfx.set_start(0).volumex(0.22)])
                        effect_applied = True
                    except:
                        pass
                        
                elif effect_type == "zoom_snap":
                    # Quick zoom-in snap at beginning of scene
                    try:
                        snap_dur = 0.25
                        def zoom_snap_fn(t):
                            if t < snap_dur:
                                progress = t / snap_dur
                                return 1.3 - 0.3 * progress  # Zoom from 1.3x to 1.0x
                            return 1.0
                        full_visual = full_visual.resize(zoom_snap_fn)
                        sfx = get_sfx('epic_hit') or get_sfx('boom') or get_sfx('bass_drop')
                        if sfx: audioclip = CompositeAudioClip([audioclip, sfx.set_start(0).volumex(0.22)])
                        effect_applied = True
                    except:
                        pass
            
            # --- SUBTITLES & TITLE ---
            scene_overlays = []
            
            # Use 'Title Box' style for the first scene (Hook/Intro) again
            is_intro_scene = (idx == 0)
            
            # Generate Subtitles
            word_clips = create_karaoke_clips(
                timings, 
                duration, 
                0, 
                width=VIDEO_WIDTH, 
                height=VIDEO_HEIGHT, 
                raw_text=text.replace('*', ''),
                is_header=is_intro_scene  # Re-enabled dynamic yellow text block on the first scene
            )
            if not word_clips and text:
                 print(f"      ⚠️ Warning: No karaoke clips generated for text: {text[:20]}...")
            
            scene_overlays.extend(word_clips)
            
            
            # Composite Scene
            scene_comp = CompositeVideoClip([full_visual.set_position("center")] + scene_overlays, size=(VIDEO_WIDTH, VIDEO_HEIGHT))
            
            # --- INTER-SCENE TRANSITIONS (Visual Overlay Only) ---
            # Add flash transition at the start of new scenes (85% chance for higher energy)
            # This overlays the flash without adding extra time/silence to the chronological timeline
            if idx > 0 and random.random() < 0.85:
                flash_t = create_flash_transition()
                flash_t = flash_t.subclip(0, min(0.2, flash_t.duration))
                scene_comp = CompositeVideoClip([scene_comp, flash_t.set_start(0)], size=(VIDEO_WIDTH, VIDEO_HEIGHT))
            
            # --- CONTEXTUAL MOOD-BASED SFX ---
            # Analyzes scene text keywords + mood to add appropriate SFX
            text_lower = text.lower()
            
            # Define keyword groups for mood detection
            horror_words = ['muerte', 'muerto', 'terror', 'horror', 'sangre', 'cadáver', 'maldición', 
                           'oscuro', 'oscuridad', 'demonio', 'fantasma', 'pesadilla', 'asesin', 'mataron',
                           'dead', 'death', 'horror', 'blood', 'curse', 'dark', 'demon', 'ghost', 'nightmare',
                           'killed', 'murder', 'terrif', 'creepy', 'haunted', 'evil', 'sinister']
            mystery_words = ['secreto', 'oculto', 'misterio', 'enigma', 'desconocido', 'nadie sabe',
                            'inexplicable', 'conspiración', 'verdad', 'escondido', 'perdido', 'olvidado',
                            'secret', 'hidden', 'mystery', 'enigma', 'unknown', 'nobody knows',
                            'inexplicable', 'conspiracy', 'truth', 'lost', 'forgotten', 'disappear']
            epic_words = ['batalla', 'guerra', 'imperio', 'conquistar', 'poder', 'legendario', 'épico',
                         'invencible', 'destruir', 'victoria', 'ejército', 'revolución', 'héroe',
                         'battle', 'war', 'empire', 'conquer', 'power', 'legendary', 'epic',
                         'invincible', 'destroy', 'victory', 'army', 'revolution', 'hero', 'warrior']
            science_words = ['descubrimiento', 'ciencia', 'tecnología', 'cerebro', 'mente', 'universo',
                            'cuántico', 'experimento', 'científico', 'laboratorio', 'átomo', 'genio',
                            'discovery', 'science', 'technology', 'brain', 'mind', 'universe',
                            'quantum', 'experiment', 'scientist', 'laboratory', 'atom', 'genius']
            sad_words = ['triste', 'llorar', 'dolor', 'sufrir', 'tragedia', 'pérdida', 'soledad',
                        'abandonado', 'desesperación', 'lamento', 'víctima',
                        'sad', 'cry', 'pain', 'suffer', 'tragedy', 'loss', 'loneliness', 'desperate']
            dramatic_words = ['increíble', 'imposible', 'impactante', 'revelación', 'sorprendente',
                             'shocking', 'mind-blowing', 'incredible', 'impossible', 'unbelievable',
                             'revolucionó', 'cambió para siempre', 'nunca antes', 'jamás', 'asombroso']
            
            # Check which mood matches this scene's text
            scene_sfx = None
            sfx_vol = 0.12
            
            if any(w in text_lower for w in horror_words) or mood == 'dark':
                scene_sfx = get_sfx('horror_stinger') or get_sfx('horror_impact') or get_sfx('horror_whisper')
                sfx_vol = 0.14
            elif any(w in text_lower for w in epic_words):
                scene_sfx = get_sfx('epic_hit') or get_sfx('dramatic_reveal')
                sfx_vol = 0.12
            elif any(w in text_lower for w in mystery_words) or mood == 'mystery':
                scene_sfx = get_sfx('mystery_tone') or get_sfx('suspense_build')
                sfx_vol = 0.10
            elif any(w in text_lower for w in science_words) or mood == 'curiosity':
                scene_sfx = get_sfx('digital_blip') or get_sfx('sci_fi_scan')
                sfx_vol = 0.10
            elif any(w in text_lower for w in sad_words) or mood == 'sad':
                scene_sfx = get_sfx('sad_tone')
                sfx_vol = 0.10
            elif any(w in text_lower for w in dramatic_words):
                scene_sfx = get_sfx('dramatic_reveal') or get_sfx('epic_hit')
                sfx_vol = 0.12
            
            # Apply contextual SFX at a random position in the scene (not always at start)
            if scene_sfx:
                sfx_start = random.uniform(0.1, max(0.2, duration * 0.3))
                audioclip = CompositeAudioClip([audioclip, scene_sfx.set_start(sfx_start).volumex(sfx_vol)])
                print(f"      🎵 Contextual SFX applied at {sfx_start:.1f}s (mood-matched)")
            
            # Add suspense build before the last 2 scenes for tension
            if idx == len(scenes) - 2:
                tension_sfx = get_sfx('suspense_build') or get_sfx('tension_riser')
                if tension_sfx:
                    # Place near end of scene to build into climax
                    t_start = max(0, duration - tension_sfx.duration - 0.2)
                    audioclip = CompositeAudioClip([audioclip, tension_sfx.set_start(t_start).volumex(0.10)])
                    print(f"      🎵 Tension build SFX at {t_start:.1f}s (pre-climax)")
            
            # Thunder SFX for dramatic moments (20% chance if text is dark/heavy)
            if any(w in text_lower for w in ['destruir', 'destroy', 'caer', 'caída', 'colapso', 'fin', 'apocal']):
                thunder = get_sfx('thunder')
                if thunder and random.random() < 0.5:
                    audioclip = CompositeAudioClip([audioclip, thunder.set_start(0.5).volumex(0.08)])
            
            scene_comp = scene_comp.set_audio(audioclip)
            final_clips.append(scene_comp)
            
            # --- MEMORY SAFETY ---
            # Explicitly clear large objects if possible
            del full_visual
            del scene_overlays
            try:
                 del scene_comp
            except:
                 pass
            import gc
            gc.collect() # OPTIMIZATION: Collect garbage ON EVERY ITERATION to prevent RAM out-of-memory crashes
            
        if not final_clips: return False

        # --- FINAL ASSEMBLY & TRANSITIONS ---
        # Instead of raw "chain", we use crossfades and dynamic sliding for a cinematic look
        if len(final_clips) > 1:
            print("      🎬 Applying cinematic crossfade transitions...")
            # Apply crossfadein to all clips except the first one
            processed_clips = [final_clips[0]]
            for i in range(1, len(final_clips)):
                # Mix of crossfade and slide/fade transitions
                t_choice = random.choice(["crossfade", "crossfade", "fade_slide"])
                c = final_clips[i]
                if t_choice == "crossfade":
                    c = c.crossfadein(0.3)
                else:
                    # Fade in with a slight brightness pop
                    c = c.fadein(0.2).fl(lambda gf, t: np.minimum(255, gf(t) * (1.2 if t < 0.1 else 1.0)).astype('uint8'))
                processed_clips.append(c)
            final_video = concatenate_videoclips(processed_clips, padding=-0.3, method="compose")
        else:
            final_video = final_clips[0]
        
        # Audio Mixing
        main_audio = final_video.audio
        audio_layers = [main_audio]

        # --- LAYER 1: Subtle Swooshes at Scene Transitions ---
        swoosh_sfx = get_sfx('swoosh')
        if swoosh_sfx:
             curr_t = 0
             for i in range(len(processed_clips)-1):
                 curr_t += processed_clips[i].duration - 0.3 # match transition padding
                 # 85% chance at each cut point for cinematic feel
                 if random.random() < 0.85: 
                      sfx_variant = get_sfx('swoosh_gen') or swoosh_sfx # Prefer generated whooshes
                      audio_layers.append(sfx_variant.set_start(max(0, curr_t)).volumex(0.25))

        # --- LAYER 2: Soft Pops/Clicks at remaining cuts ---
        pop_sfx = get_sfx('pop')
        click_sfx = get_sfx('click')
        if pop_sfx or click_sfx:
             curr_t = 0
             for i in range(len(processed_clips)-1):
                 curr_t += processed_clips[i].duration - 0.3
                 if random.random() < 0.6:
                      sfx_choice = random.choice([s for s in [pop_sfx, click_sfx] if s])
                      audio_layers.append(sfx_choice.set_start(max(0, curr_t)).volumex(0.20))

        # --- LAYER 3: Shimmer on Title (First 2 seconds) ---
        shimmer = get_sfx('shimmer')
        if shimmer:
            audio_layers.append(shimmer.set_start(0.3).volumex(0.06))

        # --- LAYER 4: Tension Riser Before Climax (last scene) ---
        if len(final_clips) >= 2:
            # Place a subtle reverse cymbal or riser before the last scene
            rev_cymbal = get_sfx('reverse_cymbal')
            if not rev_cymbal:
                rev_cymbal = get_sfx('tension_riser')
            if rev_cymbal:
                # Start it ~2s before the last scene begins
                last_scene_start = sum(c.duration for c in final_clips[:-1]) - 1.5
                if last_scene_start > 1:
                    audio_layers.append(rev_cymbal.set_start(max(0, last_scene_start)).volumex(0.07))

        # --- LAYER 5: Background Music (Mood-based) ---
        if os.path.isdir(music_dir):
            all_files = [f for f in os.listdir(music_dir) if f.endswith('.mp3')]
            
            # Smart Music Selection
            allowed_files = MUSIC_MOODS.get(mood, [])
            valid_choices = [f for f in all_files if f in allowed_files]
            
            if not valid_choices:
                print(f"⚠️ No music found for mood '{mood}'. Using random.")
                valid_choices = all_files
            
            if valid_choices:
                selected_track = random.choice(valid_choices)
                print(f"🎵 Music Selected: {selected_track} (Mood: {mood})")
                
                music = AudioFileClip(os.path.join(music_dir, selected_track))
                if music.duration < final_video.duration:
                    music = audio_loop(music, duration=final_video.duration)
                else:
                    music = music.subclip(0, final_video.duration)
                # Lower music volume to ensure voice and heavy SFX stand out (ducking simulation)
                audio_layers.append(music.volumex(0.065))
                
        # --- LAYER 6: Ambient Texture (Drone/Wind/Space) ---
        ambient_keys = [k for k in sfx_lib.keys() if 'ambient' in k or 'drone' in k or 'wind' in k or 'space' in k]
        if ambient_keys:
            amb_sfx = sfx_lib[random.choice(ambient_keys)]
            if amb_sfx.duration < final_video.duration:
                 amb_sfx = audio_loop(amb_sfx, duration=final_video.duration)
            else:
                 amb_sfx = amb_sfx.subclip(0, final_video.duration)
            audio_layers.append(amb_sfx.volumex(0.06)) # Very quiet background texture
            print(f"🌊 Ambient layer added.")
        
        final_video = final_video.set_audio(CompositeAudioClip(audio_layers))
        
        # --- MANDATORY INTRO EFFECT ---
        intro_dur = 0.5
        if style_mgr.intro_effect == "cinematic_zoom":
            # "Transicion mas linda"
            # Logic: Start Black and Zoomed In (1.2) -> Fade In and Zoom Out to (1.0)
            intro_duration = 0.8
            
            # Split into intro part and rest
            intro_part = final_video.subclip(0, intro_duration)
            rest_part = final_video.subclip(intro_duration)
            
            # Visual: Zoom Out (1.2 -> 1.0) + Fade In
            intro_part = intro_part.resize(lambda t: 1.2 - 0.2 * (t/intro_duration))
            intro_part = intro_part.fadein(0.6)
            
            final_video = concatenate_videoclips([intro_part, rest_part])
            
            # Cinematic intro SFX: Deep Boom + subtle swoosh
            sfx_boom = get_sfx('boom')
            if sfx_boom: audio_layers.append(sfx_boom.set_start(0).volumex(0.35)) # Boosted boom
            sfx_soft = get_sfx('swoosh')
            if sfx_soft: audio_layers.append(sfx_soft.set_start(0.1).volumex(0.20))

        elif style_mgr.intro_effect == "flash_in":
            flash = create_flash_transition()
            final_video = CompositeVideoClip([final_video, flash.set_start(0)], size=(VIDEO_WIDTH,VIDEO_HEIGHT))
            # Bass drop on flash intro
            sfx_intro = get_sfx('bass_drop')
            if not sfx_intro: sfx_intro = get_sfx('boom')
            if sfx_intro: audio_layers.append(sfx_intro.set_start(0).volumex(0.35))
            
        elif style_mgr.intro_effect == "glitch_start":
            # Apply glitch to first 0.5s
            intro_clip = final_video.subclip(0, 0.6)
            intro_glitch = vfx_glitch_clip(intro_clip, duration=0.6)
            final_video = CompositeVideoClip([final_video, intro_glitch.set_start(0)], size=(VIDEO_WIDTH,VIDEO_HEIGHT))
            # Louder glitch punch
            sfx_intro = get_sfx('glitch')
            if sfx_intro: audio_layers.append(sfx_intro.set_start(0).volumex(0.35))

        # Re-set audio after Intro SFX additions
        if len(audio_layers) > 1:
            final_video = final_video.set_audio(CompositeAudioClip(audio_layers))

        # --- MANDATORY OUTRO EFFECT ---
        outro_dur = 0.8
        total_dur = final_video.duration
        
        if style_mgr.outro_effect == "fade_out":
            final_video = final_video.fadeout(outro_dur)
            
        elif style_mgr.outro_effect == "burn_out":
            # Fade to white
            final_video = final_video.fadeout(outro_dur, (255,255,255))
            
        elif style_mgr.outro_effect == "glitch_out":
            start_glitch = total_dur - 0.6
            if start_glitch > 0:
                end_part = final_video.subclip(start_glitch)
                end_glitch = vfx_glitch_clip(end_part, duration=0.6)
                # Overlay
                final_video = CompositeVideoClip([final_video, end_glitch.set_start(start_glitch)], size=(VIDEO_WIDTH,VIDEO_HEIGHT))
                # Quiet glitch out
                sfx_outro = get_sfx('glitch')
                if sfx_outro: 
                     new_audio = CompositeAudioClip([final_video.audio, sfx_outro.set_start(start_glitch).volumex(0.5)])
                     final_video = final_video.set_audio(new_audio)

        if style_mgr.outro_effect == "glitch_out":
            # ... (Glitch out logic kept)
            pass

        # --- ORIGINALITY: PROGRESS BAR ---
        # "Retention Bar"
        final_video = vfx_progress_bar(final_video, color=(200, 0, 0), height=15)

        # --- ORIGINALITY: WATERMARK ---
        # Subtle branding in top-right or bottom
        try:
             # Use TextClip if ImageMagick is configured, OR use PIL ImageClip
             # Using PIL ImageClip for safety (no dependency on ImageMagick binary)
             # Load small font
             try:
                 wm_font = ImageFont.truetype(FONT_PATH, 28)
             except:
                 wm_font = ImageFont.load_default()
                 
             # Text with shadow
             wm_text = watermark_text if watermark_text else "@RapidFacts"
             
             # Calculate dynamic size based on text
             dummy_img = Image.new('RGBA', (1, 1))
             dummy_draw = ImageDraw.Draw(dummy_img)
             bbox = dummy_draw.textbbox((0, 0), wm_text, font=wm_font)
             wm_w = max(400, bbox[2] - bbox[0] + 50)
             wm_h = max(100, bbox[3] - bbox[1] + 50)
             
             wm_img = Image.new('RGBA', (wm_w, wm_h), (0,0,0,0))
             wm_draw = ImageDraw.Draw(wm_img)
             # Shadow
             wm_draw.text((22, 22), wm_text, font=wm_font, fill=(0,0,0,128))
             # Main
             wm_draw.text((20, 20), wm_text, font=wm_font, fill=(255,255,255,128)) # 50% opacity
             
             wm_array = np.array(wm_img)
             wm_clip = ImageClip(wm_array)
             
             # Extract alpha channel to use as mask
             mask_array = wm_array[:,:,3] / 255.0
             wm_mask = ImageClip(mask_array, ismask=True)
             
             wm_clip = wm_clip.set_mask(wm_mask).set_duration(final_video.duration)
             # Position: Bottom Center, slightly up
             wm_clip = wm_clip.set_position(("center", VIDEO_HEIGHT - 100))
             
             final_video = CompositeVideoClip([final_video, wm_clip], size=(VIDEO_WIDTH,VIDEO_HEIGHT))
             print(f"      💧 Watermark applied: {wm_text}")
             
        except Exception as e_wm:
             print(f"      ⚠️ Watermark error: {e_wm}")

        # Removed Global Title Overlay loop to prevent overlapping/mess ("horrible")
        # Title is now handled sequentially in the first scene loop.

        from proglog import ProgressBarLogger
        class CancelableLogger(ProgressBarLogger):
            def __init__(self, is_cancelled_func, prog_cb):
                super().__init__(init_state=None, bars=None, ignored_bars=None, logged_bars='all', min_time_interval=0, ignore_bars_under=0)
                self.is_cancelled = is_cancelled_func
                self.prog_cb = prog_cb
                
            def callback(self, **kwargs):
                if self.is_cancelled and self.is_cancelled():
                    # We raise a standard Exception that MoviePy won't catch easily
                    raise KeyboardInterrupt("Render Cancelled by User")

            def bars_callback(self, bar, attr, value, old_value):
                # Move bar progress
                if bar == 'chunk' or bar == 't':
                    if attr == 'index' and self.prog_cb:
                        total = self.bars[bar].get('total', 1)
                        if total and total > 0:
                            # Map MoviePy (0.0 - 1.0) phase to the remaining app (0.45 - 1.0) phase
                            pct = 0.45 + 0.55 * (value / total) 
                            msg = f"Encoding frames and audio... {int((value/total)*100)}%"
                            self.prog_cb(pct, status_text="Generating Final Video...", sub_text=msg)
                            
            def set_state(self, **kwargs):
                self.callback(**kwargs)
            
            # Override print message to suppress console logs
            def print_message(self, message):
                pass
            
            def set_message(self, message):
                pass

        custom_logger = CancelableLogger(is_cancelled, progress_callback)

        # OPTIMIZED WRITE: FAST PRESET, 4 THREADS, 5000k BITRATE (plenty for 720p)
        final_video.write_videofile(
            output_file, 
            fps=30, 
            codec='libx264', 
            audio_codec='aac', 
            bitrate="5000k", 
            preset='fast',        # OPTIMIZATION: Great speed/quality trade-off
            threads=4,            # OPTIMIZATION: 4 threads for faster encoding
            logger=custom_logger
        )
        # Cleanup Resources
        try:
            final_video.close()
            for c in final_clips:
                try: c.close()
                except: pass
            for s in sfx_lib.values():
                try: s.close()
                except: pass
        except:
            pass
            
        return True

    except KeyboardInterrupt:
        print("🛑 Video Assembly Cancelled.")
        # Cleanup Resources
        try:
            if 'final_video' in locals(): final_video.close()
            for c in final_clips:
                try: c.close()
                except: pass
            for s in sfx_lib.values():
                try: s.close()
                except: pass
        except:
            pass
        return False
        
    except Exception as e:
        print(f"Error assembling video: {e}")
        import traceback
        traceback.print_exc()
        return False
