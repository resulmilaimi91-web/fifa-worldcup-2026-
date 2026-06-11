import os
import sys
from moviepy import (
    ImageClip, concatenate_videoclips, CompositeVideoClip,
    TextClip, AudioFileClip, VideoFileClip, vfx
)
from moviepy.video.fx import FadeIn, FadeOut
import random
import json

BASE_DIR = os.path.dirname(__file__)
IMAGES_DIR = os.path.join(BASE_DIR, "images")
VIDEOS_DIR = os.path.join(BASE_DIR, "videos")
FRAMES_DIR = os.path.join(BASE_DIR, "reference_frames")
os.makedirs(IMAGES_DIR, exist_ok=True)
os.makedirs(VIDEOS_DIR, exist_ok=True)
os.makedirs(FRAMES_DIR, exist_ok=True)

W, H = 1920, 1080
W_SHORT = 1080
H_SHORT = 1920
FPS = 24
IMAGE_DURATION = 5.0
SHORT_IMAGE_DURATION = 3.0
TRANSITION_DURATION = 0.5

FONT_PATH = r"C:\Windows\Fonts\arial.ttf"
FONT_BOLD = r"C:\Windows\Fonts\arialbd.ttf"
FONT_SEGOE = r"C:\Windows\Fonts\segoeui.ttf"

SERIES = [
    {
        "title": "FIFA World Cup 2026\nKupa e Botes",
        "filename": "worldcup2026_ep01_intro.mp4",
        "episode": "Episodi 1",
        "description": "Mir se vini ne Boterorin 2026!",
    },
    {
        "title": "Stadiumet e Boterorit\n2026",
        "filename": "worldcup2026_ep02_stadiums.mp4",
        "episode": "Episodi 2",
        "description": "16 shtepi te futbollit",
    },
    {
        "title": "Yjet e Boterorit\n2026",
        "filename": "worldcup2026_ep03_stars.mp4",
        "episode": "Episodi 3",
        "description": "Lojtaret me te mire",
    },
    {
        "title": "Tifozet e Boterorit\nPasioni i futbollit",
        "filename": "worldcup2026_ep04_fans.mp4",
        "episode": "Episodi 4",
        "description": "Miliona zemra ne nje",
    },
    {
        "title": "Momente te paharrueshme\nFIFA 2026",
        "filename": "worldcup2026_ep05_highlights.mp4",
        "episode": "Episodi 5",
        "description": "Aksioni me i mire",
    },
]

def make_text_clip(text, font_size=60, color="white", duration=3.0, font_path=None):
    fp = font_path or FONT_BOLD
    return TextClip(
        text=text,
        font_size=font_size,
        color=color,
        stroke_color="black",
        stroke_width=2,
        font=fp,
        size=(W - 200, None),
        method="caption",
        text_align="center",
    ).with_duration(duration).with_position("center")

def make_clip(img_path, duration=IMAGE_DURATION, zoom_speed=0.015, is_short=False):
    cw, ch = (W_SHORT, H_SHORT) if is_short else (W, H)
    clip = ImageClip(img_path, duration=duration)
    clip = clip.resized(width=cw)
    if clip.h < ch:
        clip = clip.resized(height=ch)
    if clip.h > ch:
        clip = clip.cropped(y_center=clip.h / 2, height=ch)
    if clip.w > cw:
        clip = clip.cropped(x_center=clip.w / 2, width=cw)
    clip = clip.with_position("center")
    clip = clip.with_effects([vfx.ZoomIn(zoom_speed)])
    clip = clip.with_effects([FadeIn(TRANSITION_DURATION), FadeOut(TRANSITION_DURATION)])
    return clip

def create_video(ep_config, images, is_short=False):
    cw, ch = (W_SHORT, H_SHORT) if is_short else (W, H)
    img_dur = SHORT_IMAGE_DURATION if is_short else IMAGE_DURATION
    
    clips = []
    
    # Title
    tc = make_text_clip(ep_config["title"], font_size=70 if is_short else 80, color="gold", duration=4.0)
    tb = ImageClip(images[0], duration=4.0).resized(width=cw).cropped(width=cw, height=ch)
    tb = tb.with_effects([vfx.ZoomIn(0.01)])
    clips.append(CompositeVideoClip([tb, tc]))

    # Image slides
    for img_path in images:
        clip = make_clip(img_path, duration=img_dur, is_short=is_short)
        clips.append(clip)

    # Outro
    ot = make_text_clip(
        "Subscribe per me shume!",
        font_size=60 if is_short else 70, color="gold", duration=4.0
    )
    ob = ImageClip(images[-1], duration=4.0).resized(width=cw).cropped(width=cw, height=ch)
    ob = ob.with_effects([vfx.ZoomIn(0.01)])
    clips.append(CompositeVideoClip([ob, ot]))

    final = concatenate_videoclips(clips, method="compose")
    
    suffix = "_short" if is_short else ""
    out = os.path.join(VIDEOS_DIR, ep_config["filename"].replace(".mp4", f"{suffix}.mp4"))
    print(f"  Rendering: {out} ({final.duration/60:.1f} min)")
    final.write_videofile(
        out, fps=FPS, codec="libx264", audio_codec=False,
        bitrate="4000k", preset="medium", threads=2, logger=None
    )
    return out

def extract_frames_from_reference(video_path, output_dir, num_frames=20):
    if not os.path.exists(video_path):
        print(f"  Reference video not found: {video_path}")
        return []
    
    print(f"  Extracting {num_frames} frames from reference video...")
    try:
        clip = VideoFileClip(video_path)
        dur = clip.duration
        frame_paths = []
        for i in range(num_frames):
            t = (i + 0.5) * dur / num_frames
            frame = clip.get_frame(t)
            from PIL import Image
            import numpy as np
            img = Image.fromarray(np.uint8(frame))
            fp = os.path.join(output_dir, f"ref_frame_{i+1:02d}.jpg")
            img.save(fp, quality=85)
            frame_paths.append(fp)
        clip.close()
        print(f"  Extracted {len(frame_paths)} frames to {output_dir}")
        return frame_paths
    except Exception as e:
        print(f"  Error extracting frames: {e}")
        return []

def load_images():
    exts = {'.jpg', '.jpeg', '.png', '.webp'}
    imgs = sorted([
        os.path.join(IMAGES_DIR, f) for f in os.listdir(IMAGES_DIR)
        if os.path.splitext(f)[1].lower() in exts
    ])
    return imgs

def main():
    print("=" * 60)
    print("FIFA World Cup 2026 - YouTube Content Generator")
    print("=" * 60)
    
    # Extract frames from reference FIFA video
    ref_video = r"C:\Users\User\Downloads\fifa2026_preview_ep11.f137.mp4"
    ref_frames = extract_frames_from_reference(ref_video, FRAMES_DIR, 20)

    # Load images
    all_images = load_images()
    if len(all_images) < 5:
        print(f"Warning: Only {len(all_images)} images. Copying reference frames to images dir...")
        for f in ref_frames:
            dst = os.path.join(IMAGES_DIR, os.path.basename(f))
            if not os.path.exists(dst):
                import shutil
                shutil.copy(f, dst)
        all_images = load_images()
    
    print(f"Images available: {len(all_images)}")
    
    if len(all_images) < 3:
        print("Not enough images. Exiting.")
        return

    for ep in SERIES:
        random.seed(ep["episode"])
        random.shuffle(all_images)
        selected = all_images[:min(25, len(all_images))]
        
        print(f"\n--- {ep['episode']}: {ep['title']} ---")
        
        # Long video
        create_video(ep, selected, is_short=False)
        
        # Short
        short_imgs = selected[:min(10, len(selected))]
        create_video(ep, short_imgs, is_short=True)

    print(f"\n{'='*60}")
    print(f"ALL VIDEOS CREATED!")
    print(f"Folder: {VIDEOS_DIR}")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
