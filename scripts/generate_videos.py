import os, sys, json, random, subprocess, shutil, asyncio, argparse

BASE = os.path.dirname(os.path.dirname(__file__))
IMAGES_DIR = os.path.join(BASE, "images")
VIDEOS_DIR = os.path.join(BASE, "videos")
DATA_FILE = os.path.join(BASE, "data", "worldcup2026.json")
TTS_DIR = os.path.join(BASE, "tmp_tts")
os.makedirs(VIDEOS_DIR, exist_ok=True)
os.makedirs(TTS_DIR, exist_ok=True)

FPS = 24
W, H = 1920, 1080

def ffmpeg():
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return "ffmpeg"

def load_data():
    with open(DATA_FILE, encoding="utf-8") as f:
        return json.load(f)

def load_images():
    exts = {".jpg", ".jpeg", ".png"}
    return sorted([
        os.path.join(IMAGES_DIR, f) for f in os.listdir(IMAGES_DIR)
        if os.path.splitext(f)[1].lower() in exts
    ])

def gen_tts(text, output, voice="sq-AL-IlirNeural"):
    asyncio.run(__import__("edge_tts").Communicate(text, voice=voice).save(output))
    return output

def gen_bg_music(output, duration_sec, volume=0.08):
    """Generate copyright-free ambient background music using FFmpeg"""
    ff = ffmpeg()
    subprocess.run([
        ff, "-y",
        "-f", "lavfi", "-i", f"anoisesrc=d={duration_sec}:c=pink:a=0.5",
        "-f", "lavfi", "-i", f"sine=frequency=220:duration={duration_sec}",
        "-filter_complex",
        f"[0:a]volume={volume}[a];[1:a]volume={volume/2}[b];[a][b]amix=inputs=2:duration=first",
        "-ac", "1", "-ar", "22050", output
    ], capture_output=True, timeout=120)

def prep_image(src, dst, w=W, h=H):
    subprocess.run([
        ffmpeg(), "-y", "-i", src,
        "-vf", f"scale={w}:{h}:force_original_aspect_ratio=1,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:color=black",
        "-qscale:v", "2", dst
    ], capture_output=True, timeout=60)

def make_video(images, output, audio=None, duration_per_img=3.0,
               title_text=None, subtitle_text=None):
    """Create video from images with Ken Burns zoom, optional title and audio"""
    ff = ffmpeg()
    tmp = os.path.join(BASE, "tmp_vid")
    os.makedirs(tmp, exist_ok=True)

    # Resize images
    resized = []
    for i, img in enumerate(images):
        dst = os.path.join(tmp, f"r_{i:03d}.jpg")
        prep_image(img, dst)
        resized.append(dst)

    # Create individual video segments with zoom effect
    segs = []
    for i, img in enumerate(resized):
        out = os.path.join(tmp, f"s_{i:03d}.mp4")
        # Ken Burns zoom: start at 1.0x, end at 1.05x over duration
        dur = duration_per_img + 0.3
        cmd = [
            ff, "-y", "-loop", "1", "-i", img,
            "-vf",
            f"fps={FPS},zoompan=z='min(zoom+0.0015,1.05)':d={int(FPS*dur)}:s={W}x{H}:fps={FPS}",
            "-c:v", "libx264", "-t", str(dur),
            "-pix_fmt", "yuv420p", "-preset", "fast", "-crf", "23",
            out
        ]
        subprocess.run(cmd, capture_output=True, timeout=120)
        segs.append(out)

    # Concat video segments
    concat_file = os.path.join(tmp, "concat.txt")
    with open(concat_file, "w") as f:
        for s in segs:
            f.write(f"file '{os.path.abspath(s)}'\n")

    video_raw = os.path.join(tmp, "concat.mp4")
    subprocess.run([
        ff, "-y", "-f", "concat", "-safe", "0",
        "-i", concat_file, "-c", "copy", video_raw
    ], capture_output=True, timeout=300)

    # Add title/subtitle overlay
    if title_text:
        escaped_title = title_text.replace(":", "\\:").replace("'", "\\\\'").replace("\n", "\\n")
        escaped_sub = subtitle_text.replace(":", "\\:").replace("'", "\\\\'").replace("\n", "\\n") if subtitle_text else ""

        filter_parts = []
        # Title at top center
        filter_parts.append(
            f"drawtext=text='{escaped_title}':"
            f"fontsize=52:fontcolor=gold:"
            f"x=(w-text_w)/2:y=h*0.08:"
            f"box=1:boxcolor=black@0.5:boxborderw=15:"
            f"fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        )
        if subtitle_text:
            filter_parts.append(
                f"drawtext=text='{escaped_sub}':"
                f"fontsize=32:fontcolor=white:"
                f"x=(w-text_w)/2:y=h*0.16:"
                f"box=1:boxcolor=black@0.4:boxborderw=10:"
                f"fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
            )

        video_with_text = os.path.join(tmp, "with_text.mp4")
        subprocess.run([
            ff, "-y", "-i", video_raw,
            "-vf", ",".join(filter_parts),
            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            video_with_text
        ], capture_output=True, timeout=300)
        video_raw = video_with_text

    # Add audio if provided
    if audio and os.path.exists(audio):
        final_out = output
        subprocess.run([
            ff, "-y", "-i", video_raw, "-i", audio,
            "-c:v", "copy", "-c:a", "aac", "-b:a", "128k",
            "-shortest", final_out
        ], capture_output=True, timeout=300)
    else:
        shutil.copy(video_raw, output)

    shutil.rmtree(tmp, ignore_errors=True)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("count", nargs="?", default="5")
    args = parser.parse_args()
    count = min(int(args.count), 5)

    print("=" * 55)
    print("FIFA World Cup 2026 - Full Video Generator")
    print("=" * 55)

    data = load_data()
    episodes = data["episodes"][:count]

    images = load_images()
    print(f"Images: {len(images)}")
    if len(images) < 5:
        print("Not enough images. Run scripts/download_images.py first.")
        return

    for ep in episodes:
        eid = ep["id"]
        title = ep["title"]
        subtitle = ep["subtitle"]
        script = ep["script"]
        ep_name = f"Episodi {eid}"

        print(f"\n--- {ep_name}: {title} ---")

        # select shuffled images
        random.seed(ep_name)
        random.shuffle(images)
        sel_imgs = images[:min(12, len(images))]
        short_imgs = sel_imgs[:min(6, len(sel_imgs))]

        # Generate TTS narration
        tts_file = os.path.join(TTS_DIR, f"narration_{eid}.mp3")
        print(f"  Generating TTS narration ({len(script)} chars)...")
        try:
            gen_tts(script, tts_file)
        except Exception as e:
            print(f"  TTS failed: {e}")
            tts_file = None

        # Generate background music (duration = images * duration_per_img + 4s title)
        dur_long = len(sel_imgs) * 3.0 + 4.0
        dur_short = len(short_imgs) * 3.0 + 3.0
        bgm_long = os.path.join(TTS_DIR, f"bgm_{eid}_long.mp3")
        bgm_short = os.path.join(TTS_DIR, f"bgm_{eid}_short.mp3")

        # Check if audio already exists
        if not os.path.exists(bgm_long):
            gen_bg_music(bgm_long, dur_long)
        if not os.path.exists(bgm_short):
            gen_bg_music(bgm_short, dur_short)

        # Mix narration + background music
        audio_long = None
        audio_short = None
        if tts_file and os.path.exists(tts_file):
            mixed_long = os.path.join(TTS_DIR, f"audio_{eid}_long.mp3")
            mixed_short = os.path.join(TTS_DIR, f"audio_{eid}_short.mp3")
            ff = ffmpeg()
            # Mix: narration (full volume) + bgm (low volume)
            for bgm, mixed, dur in [(bgm_long, mixed_long, dur_long), (bgm_short, mixed_short, dur_short)]:
                subprocess.run([
                    ff, "-y", "-i", tts_file, "-i", bgm,
                    "-filter_complex",
                    f"[1:a]volume=0.08[bgm];[0:a][bgm]amix=inputs=2:duration=first",
                    "-ac", "1", "-ar", "22050", "-t", str(dur),
                    mixed
                ], capture_output=True, timeout=120)
            audio_long = mixed_long
            audio_short = mixed_short

        # Generate long video
        out_long = os.path.join(VIDEOS_DIR, f"worldcup2026_episodi_{eid}.mp4")
        make_video(sel_imgs, out_long, audio=audio_long,
                   duration_per_img=3.0, title_text=title, subtitle_text=subtitle)
        print(f"  Long video OK: {out_long}")

        # Generate short
        out_short = os.path.join(VIDEOS_DIR, f"worldcup2026_episodi_{eid}_short.mp4")
        make_video(short_imgs, out_short, audio=audio_short,
                   duration_per_img=2.5, title_text=title)
        print(f"  Short video OK: {out_short}")

    # Cleanup TTS temp
    shutil.rmtree(TTS_DIR, ignore_errors=True)
    print(f"\n{'=' * 55}")
    print(f"Te gjitha videot gati ne {VIDEOS_DIR}!")
    print(f"{'=' * 55}")

if __name__ == "__main__":
    main()
