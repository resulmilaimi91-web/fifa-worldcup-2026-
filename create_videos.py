import os
import sys
from moviepy import (
    ImageClip, concatenate_videoclips, CompositeVideoClip,
    TextClip, AudioFileClip, afx, vfx
)
from moviepy.video.fx import FadeIn, FadeOut
import random

IMAGES_DIR = os.path.join(os.path.dirname(__file__), "images")
VIDEOS_DIR = os.path.join(os.path.dirname(__file__), "videos")
MUSIC_DIR = os.path.join(os.path.dirname(__file__), "music")
os.makedirs(VIDEOS_DIR, exist_ok=True)

W, H = 1920, 1080
FPS = 24
IMAGE_DURATION = 7.0
TRANSITION_DURATION = 0.8

SERIES = [
    {
        "title": "FIFA World Cup 2026\nKupa e Botes",
        "subtitle": "Boteri Futbollistik",
        "filename": "worldcup2026_ep01_intro.mp4",
        "episode": "Episodi 1",
        "description": "Mir se vini ne Boterorin 2026!",
        "theme": "overview"
    },
    {
        "title": "Stadiumet e Boterorit 2026\nUSA - Mexico - Canada",
        "subtitle": "16 shtepi te futbollit",
        "filename": "worldcup2026_ep02_stadiums.mp4",
        "episode": "Episodi 2",
        "description": "Nga Meksi ne Kanada",
        "theme": "stadiums"
    },
    {
        "title": "Yjet e Boterorit 2026\nLojtaret me te mire",
        "subtitle": "Yjet qe shkelqejne",
        "filename": "worldcup2026_ep03_stars.mp4",
        "episode": "Episodi 3",
        "description": "Futbollistet me te mire ne bote",
        "theme": "players"
    },
    {
        "title": "Tifozet e Boterorit\nPasioni i futbollit",
        "subtitle": "Miliona zemra ne nje",
        "filename": "worldcup2026_ep04_fans.mp4",
        "episode": "Episodi 4",
        "description": "Tifozet qe e bejne special futbollin",
        "theme": "fans"
    },
    {
        "title": "Momente te paharrueshme\nFIFA World Cup 2026",
        "subtitle": "Historia e nje Kup Bote",
        "filename": "worldcup2026_ep05_highlights.mp4",
        "episode": "Episodi 5",
        "description": "Aksioni me i mire i Boterorit",
        "theme": "highlights"
    },
]

def get_images_for_theme(theme):
    all_images = sorted([
        os.path.join(IMAGES_DIR, f) for f in os.listdir(IMAGES_DIR)
        if f.lower().endswith(('.jpg', '.jpeg', '.png'))
    ])
    random.seed(hash(theme) % (2**32))
    random.shuffle(all_images)
    return all_images[:20]

def make_clip(image_path, texts=None, zoom_dir="in"):
    clip = ImageClip(image_path, duration=IMAGE_DURATION)
    clip = clip.resized(width=W)

    if clip.h < H:
        clip = clip.resized(height=H)
    if clip.h > H:
        clip = clip.cropped(y_center=clip.h/2, height=H)
    if clip.w > W:
        clip = clip.cropped(x_center=clip.w/2, width=W)

    clip = clip.with_position(("center", "center"))

    zoom_in = vfx.ZoomIn(0.02)
    clip = clip.with_effects([zoom_in])

    clip = clip.with_effects([FadeIn(TRANSITION_DURATION), FadeOut(TRANSITION_DURATION)])

    return clip

def make_text_clip(text, font_size=60, color="white", position=("center", "center"), duration=3.0, stroke_width=2):
    return TextClip(
        text=text,
        font_size=font_size,
        color=color,
        stroke_color="black",
        stroke_width=stroke_width,
        font="Arial",
        size=(W * 0.8, None),
        method="caption",
        text_align="center",
    ).with_duration(duration).with_position(position)

def create_video(episode_config, images):
    print(f"\n{'='*60}")
    print(f"Krijimi i videos: {episode_config['episode']}")
    print(f"Titulli: {episode_config['title']}")
    print(f"{'='*60}")

    clips = []

    title_clip = make_text_clip(
        episode_config["title"],
        font_size=80,
        color="gold",
        position=("center", "center"),
        duration=5.0,
        stroke_width=3
    )
    title_bg = ImageClip(
        images[0] if images else None,
        duration=5.0
    ).resized(width=W).cropped(width=W, height=H)
    title_bg = title_bg.with_effects([vfx.ZoomIn(0.01)])
    title_comp = CompositeVideoClip([title_bg, title_clip])
    clips.append(title_comp)

    for i, img_path in enumerate(images):
        clip = make_clip(img_path)
        clips.append(clip)

    outro_text = make_text_clip(
        "Faleminderit per shikimin!\nSubscribe per me shume",
        font_size=70,
        color="gold",
        position=("center", "center"),
        duration=5.0,
        stroke_width=3
    )
    outro_bg = ImageClip(
        images[-1] if images else None,
        duration=5.0
    ).resized(width=W).cropped(width=W, height=H)
    outro_bg = outro_bg.with_effects([vfx.ZoomIn(0.01)])
    outro_comp = CompositeVideoClip([outro_bg, outro_text])
    clips.append(outro_comp)

    print(f"  Duke kombinuar {len(clips)} clips...")
    final = concatenate_videoclips(clips, method="compose")

    output_path = os.path.join(VIDEOS_DIR, episode_config["filename"])
    print(f"  Duke renderuar: {output_path}")
    final.write_videofile(
        output_path,
        fps=FPS,
        codec="libx264",
        audio_codec=False,
        bitrate="5000k",
        preset="medium",
        threads=2,
        logger=None
    )

    duration = final.duration
    print(f"  [GATI] {output_path}")
    print(f"  Duration: {duration/60:.1f} minuta")
    return output_path

def main():
    print("=" * 60)
    print("FIFA World Cup 2026 - Video Series Generator")
    print("=" * 60)

    all_images = sorted([
        os.path.join(IMAGES_DIR, f) for f in os.listdir(IMAGES_DIR)
        if f.lower().endswith(('.jpg', '.jpeg', '.png'))
    ])

    if len(all_images) < 5:
        print(f"Gabim: Vetem {len(all_images)} imazhe ne {IMAGES_DIR}")
        print("Duhen te pakten 5 imazhe. Shkarko imazhe fillimisht.")
        sys.exit(1)

    print(f"Imazhe te gatshme: {len(all_images)}")

    for ep_config in SERIES:
        random.seed(ep_config["theme"])
        random.shuffle(all_images)
        selected = all_images[:20]
        if len(selected) < 5:
            selected = all_images
        create_video(ep_config, selected)

    print(f"\n{'='*60}")
    print(f"TE GJITHA VIDEOT JANE KRIJUAR!")
    print(f"Folder: {VIDEOS_DIR}")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
