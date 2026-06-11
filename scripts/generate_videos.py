import os
import sys
import random
import argparse
import subprocess
import shutil
import json

BASE = os.path.dirname(os.path.dirname(__file__))
IMAGES_DIR = os.path.join(BASE, "images")
VIDEOS_DIR = os.path.join(BASE, "videos")
FRAMES_DIR = os.path.join(BASE, "reference_frames")
os.makedirs(VIDEOS_DIR, exist_ok=True)
os.makedirs(FRAMES_DIR, exist_ok=True)

SERIES = [
    {"title": "FIFA World Cup 2026 - Kupa e Botes", "episode": "Episodi 1"},
    {"title": "Stadiumet e Boterorit 2026", "episode": "Episodi 2"},
    {"title": "Yjet e Boterorit 2026", "episode": "Episodi 3"},
    {"title": "Tifozet e Boterorit - Pasioni i futbollit", "episode": "Episodi 4"},
    {"title": "Momente te paharrueshme FIFA 2026", "episode": "Episodi 5"},
]

def get_ffmpeg():
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except (ImportError, RuntimeError):
        for p in [r"C:\Windows\ffmpeg.exe", r"C:\ffmpeg\bin\ffmpeg.exe"]:
            if os.path.exists(p): return p
        return "ffmpeg"

def resize_image_for_ffmpeg(src, dst, w=1920, h=1080):
    """Resize image to exact dimensions using ffmpeg (fast)"""
    ffmpeg = get_ffmpeg()
    cmd = [ffmpeg, "-y", "-i", src,
           "-vf", f"scale={w}:{h}:force_original_aspect_ratio=1,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:color=black",
           "-qscale:v", "2", dst]
    subprocess.run(cmd, capture_output=True, timeout=60)

def create_slideshow_ffmpeg(image_paths, output, img_dur=3.0, transition=0.5):
    """Create video from images using FFmpeg with transitions"""
    ffmpeg = get_ffmpeg()
    tmp = os.path.join(BASE, "tmp_slideshow")
    os.makedirs(tmp, exist_ok=True)

    # Resize all images to 1920x1080
    resized = []
    for i, img in enumerate(image_paths):
        dst = os.path.join(tmp, f"img_{i:03d}.jpg")
        resize_image_for_ffmpeg(img, dst)
        resized.append(dst)

    # Build filter_complex for crossfade
    n = len(resized)
    if n == 0:
        print("  No images!")
        return

    # Use concat protocol with individual inputs
    # Each image shown for img_dur seconds
    # Crossfade between consecutive images

    # Step 1: Create individual video files for each image
    indiv_files = []
    for i, img in enumerate(resized):
        out = os.path.join(tmp, f"seg_{i:03d}.mp4")
        dur = img_dur + transition
        cmd = [ffmpeg, "-y", "-loop", "1", "-i", img,
               "-c:v", "libx264", "-t", str(dur),
               "-pix_fmt", "yuv420p", "-preset", "fast", "-crf", "23",
               "-vf", f"fps=24,settb=1/24",
               out]
        subprocess.run(cmd, capture_output=True, timeout=120)
        indiv_files.append(out)

    # Step 2: Create concat file
    concat_file = os.path.join(tmp, "concat.txt")
    with open(concat_file, "w") as f:
        for vf in indiv_files:
            f.write(f"file '{os.path.abspath(vf)}'\n")

    cmd = [ffmpeg, "-y", "-f", "concat", "-safe", "0",
           "-i", concat_file,
           "-c", "copy",
           output]
    subprocess.run(cmd, capture_output=True, timeout=300)
    shutil.rmtree(tmp, ignore_errors=True)

def extract_frames_fast(video_path, out_dir, n=15):
    """Extract frames using FFmpeg (fast)"""
    if not os.path.exists(video_path):
        print(f"  Reference not found: {video_path}")
        return []

    ffmpeg = get_ffmpeg()
    dur_cmd = [ffmpeg, "-i", video_path, "-f", "null", "-"]
    result = subprocess.run(dur_cmd, capture_output=True, text=True, timeout=60)
    dur = 0
    for line in result.stderr.split("\n"):
        if "Duration" in line:
            parts = line.strip().split(",")[0].split("Duration:")[-1].strip()
            h, m, s = parts.split(":")
            dur = int(h) * 3600 + int(m) * 60 + float(s)
            break

    if dur <= 0:
        dur = 1475  # fallback if can't parse

    frames = []
    for i in range(n):
        t = (i + 0.5) * dur / n
        fp = os.path.join(out_dir, f"ref_{i+1:02d}.jpg")
        cmd = [ffmpeg, "-y", "-ss", str(t), "-i", video_path,
               "-vframes", "1", "-qscale:v", "2", fp]
        subprocess.run(cmd, capture_output=True, timeout=30)
        frames.append(fp)
    print(f"  Extracted {n} frames")
    return frames

def load_images():
    exts = {'.jpg', '.jpeg', '.png'}
    return sorted([
        os.path.join(IMAGES_DIR, f) for f in os.listdir(IMAGES_DIR)
        if os.path.splitext(f)[1].lower() in exts
    ])

def main():
    parser = argparse.ArgumentParser(description="Generate FIFA 2026 videos")
    parser.add_argument("episodes", nargs="?", default="5", help="Number of episodes (1-5)")
    parser.add_argument("--no-git", action="store_true", help="Skip git init")
    args = parser.parse_args()
    count = min(int(args.episodes), 5)

    # Try to extract frames from FIFA reference (optional)
    ref = r"C:\Users\User\Downloads\fifa2026_preview_ep11.f137.mp4"
    try:
        ref_frames = extract_frames_fast(ref, FRAMES_DIR, 10)
        for f in ref_frames:
            dst = os.path.join(IMAGES_DIR, os.path.basename(f))
            if not os.path.exists(dst):
                shutil.copy(f, dst)
    except Exception as e:
        print(f"  Reference extraction skipped: {e}")

    imgs = load_images()
    print(f"Images: {len(imgs)}")

    if len(imgs) < 3:
        print("Not enough images!")
        return

    for ep in SERIES[:count]:
        random.seed(ep["episode"])
        random.shuffle(imgs)
        sel = imgs[:min(12, len(imgs))]
        print(f"\n--- {ep['episode']}: {ep['title']} ---")

        # Long video (~3 min = 12 images * 15s each)
        out_l = os.path.join(VIDEOS_DIR, f"worldcup2026_{ep['episode'].lower().replace(' ', '_')}.mp4")
        create_slideshow_ffmpeg(sel, out_l, img_dur=15.0)
        print(f"  OK: {out_l}")

        # Short (~1 min = 6 images * 10s each)
        short_sel = sel[:min(6, len(sel))]
        out_s = os.path.join(VIDEOS_DIR, f"worldcup2026_{ep['episode'].lower().replace(' ', '_')}_short.mp4")
        create_slideshow_ffmpeg(short_sel, out_s, img_dur=10.0)
        print(f"  OK: {out_s}")

    print(f"\nDone! Videos in {VIDEOS_DIR}")

if __name__ == "__main__":
    main()
