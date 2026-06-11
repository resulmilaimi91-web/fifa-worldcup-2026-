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

def gen_bg_music(output, duration_sec, volume=0.06):
    ff = ffmpeg()
    # Gentle ambient pad with bass pulse
    subprocess.run([
        ff, "-y",
        "-f", "lavfi", "-i", f"anoisesrc=d={duration_sec}:c=pink:a=0.4",
        "-f", "lavfi", "-i", f"sine=frequency=110:duration={duration_sec}",
        "-f", "lavfi", "-i", f"sine=frequency=165:duration={duration_sec}",
        "-filter_complex",
        f"[0:a]volume={volume}[a];"
        f"[1:a]volume={volume*0.3},afade=t=in:d=2[b];"
        f"[2:a]volume={volume*0.15},afade=t=in:d=4[c];"
        f"[a][b]amix=inputs=2:duration=first[ab];"
        f"[ab][c]amix=inputs=2:duration=first",
        "-ac", "1", "-ar", "22050", output
    ], capture_output=True, timeout=120)

def prep_image(src, dst, w=W, h=H):
    subprocess.run([
        ffmpeg(), "-y", "-i", src,
        "-vf", f"scale={w}:{h}:force_original_aspect_ratio=1,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:color=black",
        "-qscale:v", "2", dst
    ], capture_output=True, timeout=60)

def make_video_segment(images, output, duration_per_img=3.5, fps=FPS):
    """Create video from images with Ken Burns zoom, returns output path"""
    ff = ffmpeg()
    seg_dir = os.path.join(BASE, "tmp_seg")
    os.makedirs(seg_dir, exist_ok=True)

    resized = []
    for i, img in enumerate(images):
        dst = os.path.join(seg_dir, f"r_{i:03d}.jpg")
        prep_image(img, dst)
        resized.append(dst)

    segs = []
    for i, img in enumerate(resized):
        out = os.path.join(seg_dir, f"s_{i:03d}.mp4")
        dur = duration_per_img + 0.3
        cmd = [
            ff, "-y", "-loop", "1", "-i", img,
            "-vf",
            f"fps={fps},zoompan=z='min(zoom+0.002,1.06)':d={int(fps*dur)}:s={W}x{H}:fps={fps}",
            "-c:v", "libx264", "-t", str(dur),
            "-pix_fmt", "yuv420p", "-preset", "fast", "-crf", "23",
            out
        ]
        subprocess.run(cmd, capture_output=True, timeout=120)
        segs.append(out)

    concat = os.path.join(seg_dir, "c.txt")
    with open(concat, "w") as f:
        for s in segs:
            f.write(f"file '{os.path.abspath(s)}'\n")

    out_raw = os.path.join(seg_dir, "concat.mp4")
    subprocess.run([
        ff, "-y", "-f", "concat", "-safe", "0",
        "-i", concat, "-c", "copy", out_raw
    ], capture_output=True, timeout=300)

    shutil.copy(out_raw, output)
    shutil.rmtree(seg_dir, ignore_errors=True)
    return output

def add_fifa_style_overlay(input_video, output_video, text_lines, duration_sec=None):
    """Add FIFA-style lower third text overlays (dark bar + text at bottom-left)"""
    ff = ffmpeg()
    # Filter to draw: black bar at bottom, then text on top
    bar_h = 80
    filters = [
        # Black semi-transparent bar at bottom
        f"drawbox=x=0:y=ih-{bar_h}:w=iw:h={bar_h}:color=black@0.65:t=fill"
    ]

    # Add text lines in the bar
    y_pos = H - bar_h + 12
    bold_font = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    reg_font = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

    for i, line in enumerate(text_lines):
        escaped = line.replace(":", "\\:").replace("'", "\\\\'").replace("\n", "\\n")
        fontsize = 36 if i == 0 else 26
        font_file = bold_font if i == 0 else reg_font
        color = "gold" if i == 0 else "white"
        y_off = y_pos + i * 32
        filters.append(
            f"drawtext=text='{escaped}':"
            f"fontfile={font_file}:"
            f"fontsize={fontsize}:fontcolor={color}:"
            f"x=30:y={y_off}"
        )

    subprocess.run([
        ff, "-y", "-i", input_video,
        "-vf", ",".join(filters),
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        output_video
    ], capture_output=True, timeout=300)

def add_title_card(input_video, output_video, title, subtitle=None):
    """Add centered title card overlay"""
    ff = ffmpeg()
    filters = [
        # Semi-transparent overlay
        f"drawbox=x=0:y=0:w=iw:h=ih:color=black@0.5:t=fill",
        # Title
        f"drawtext=text='{title.replace(":", '\\:')}':"
        f"fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:"
        f"fontsize=56:fontcolor=gold:"
        f"x=(w-text_w)/2:y=(h-text_h)/2-40:"
        f"box=1:boxcolor=black@0.4:boxborderw=15"
    ]
    if subtitle:
        filters.append(
            f"drawtext=text='{subtitle.replace(":", '\\:')}':"
            f"fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf:"
            f"fontsize=32:fontcolor=white:"
            f"x=(w-text_w)/2:y=(h-text_h)/2+30"
        )

    subprocess.run([
        ff, "-y", "-i", input_video,
        "-vf", ",".join(filters),
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        output_video
    ], capture_output=True, timeout=300)

def concat_videos(video_list, output):
    ff = ffmpeg()
    tmp = os.path.join(BASE, "tmp_cat")
    os.makedirs(tmp, exist_ok=True)
    concat_file = os.path.join(tmp, "c.txt")
    with open(concat_file, "w") as f:
        for v in video_list:
            if os.path.exists(v):
                f.write(f"file '{os.path.abspath(v)}'\n")
    subprocess.run([
        ff, "-y", "-f", "concat", "-safe", "0",
        "-i", concat_file, "-c", "copy", output
    ], capture_output=True, timeout=300)
    shutil.rmtree(tmp, ignore_errors=True)

def mix_audio(tts_file, bgm_file, output, duration_sec=None):
    """Mix TTS (full volume) with BGM (low volume)"""
    ff = ffmpeg()
    cmd = [
        ff, "-y", "-i", tts_file, "-i", bgm_file,
        "-filter_complex",
        "[1:a]volume=0.08[bgm];[0:a][bgm]amix=inputs=2:duration=first",
        "-ac", "1", "-ar", "22050"
    ]
    if duration_sec:
        cmd += ["-t", str(duration_sec)]
    cmd.append(output)
    subprocess.run(cmd, capture_output=True, timeout=120)

def get_duration(video_path):
    ff = ffmpeg()
    result = subprocess.run([ff, "-i", video_path, "-f", "null", "-"],
                            capture_output=True, text=True, timeout=60)
    for line in result.stderr.split("\n"):
        if "Duration" in line:
            parts = line.strip().split(",")[0].split("Duration:")[-1].strip()
            h, m, s = parts.split(":")
            return int(h) * 3600 + int(m) * 60 + float(s)
    return 0

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("count", nargs="?", default="5")
    args = parser.parse_args()
    count = min(int(args.count), 5)

    print("=" * 55)
    print("FIFA World Cup 2026 - Channel Style Generator")
    print("Follows FIFA Preview Series format")
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
        scripts = ep["script"]
        ep_name = f"Episodi {eid}"

        print(f"\n--- {ep_name}: {title} ---")

        # Select images - split across script segments
        random.seed(ep_name)
        random.shuffle(images)
        segment_count = len(scripts)
        imgs_per_seg = max(4, min(8, len(images) // segment_count))

        video_segments = []

        for seg_idx, script_text in enumerate(scripts):
            start = seg_idx * imgs_per_seg
            end = start + imgs_per_seg
            seg_imgs = images[start:end]
            if not seg_imgs:
                seg_imgs = images[:4]
            print(f"  Segment {seg_idx+1}: {len(seg_imgs)} images, narration {len(script_text)} chars")

            # Generate raw video for this segment
            raw_vid = os.path.join(TTS_DIR, f"raw_{eid}_{seg_idx}.mp4")
            make_video_segment(seg_imgs, raw_vid, duration_per_img=3.5)

            # Add FIFA-style lower third overlay
            styled_vid = os.path.join(TTS_DIR, f"styled_{eid}_{seg_idx}.mp4")
            add_fifa_style_overlay(raw_vid, styled_vid, [title, f"{ep_name} | Analiza"])

            # Add title card at start
            titled_vid = os.path.join(TTS_DIR, f"titled_{eid}_{seg_idx}.mp4")
            add_title_card(styled_vid, titled_vid, title, subtitle)

            video_segments.append(titled_vid)

        # Concatenate all segments
        concat_vid = os.path.join(TTS_DIR, f"concat_{eid}.mp4")
        concat_videos(video_segments, concat_vid)

        vid_dur = get_duration(concat_vid)
        print(f"  Total video duration: {vid_dur:.1f}s ({vid_dur/60:.1f} min)")

        # Generate TTS for each segment
        tts_segments = []
        for seg_idx, script_text in enumerate(scripts):
            tts_file = os.path.join(TTS_DIR, f"tts_{eid}_{seg_idx}.mp3")
            try:
                gen_tts(script_text, tts_file)
                tts_segments.append(tts_file)
            except Exception as e:
                print(f"  TTS failed for segment {seg_idx}: {e}")

        # Mix TTS with BGM
        if tts_segments:
            # Concatenate TTS segments
            tts_all = os.path.join(TTS_DIR, f"tts_all_{eid}.mp3")
            concat_file = os.path.join(TTS_DIR, "tts_concat.txt")
            with open(concat_file, "w") as f:
                for ts in tts_segments:
                    if os.path.exists(ts):
                        f.write(f"file '{os.path.abspath(ts)}'\n")
            subprocess.run([
                ffmpeg(), "-y", "-f", "concat", "-safe", "0",
                "-i", concat_file, "-c", "copy", tts_all
            ], capture_output=True, timeout=120)

            # Generate BGM for video duration
            bgm = os.path.join(TTS_DIR, f"bgm_{eid}.mp3")
            gen_bg_music(bgm, max(vid_dur, 30))

            # Mix
            mixed = os.path.join(TTS_DIR, f"audio_{eid}.mp3")
            mix_audio(tts_all, bgm, mixed, duration_sec=vid_dur)

            # Final render: video + audio
            final_long = os.path.join(VIDEOS_DIR, f"worldcup2026_episodi_{eid}.mp4")
            subprocess.run([
                ffmpeg(), "-y", "-i", concat_vid, "-i", mixed,
                "-c:v", "copy", "-c:a", "aac", "-b:a", "128k",
                "-shortest", final_long
            ], capture_output=True, timeout=300)
            print(f"  OK: {final_long}")

        # Short version (just first segment + images)
        short_vid = os.path.join(TTS_DIR, f"short_{eid}.mp4")
        if len(video_segments) >= 1:
            shutil.copy(video_segments[0], short_vid)
        else:
            make_video_segment(images[:6], short_vid, duration_per_img=2.5)

        if tts_segments:
            short_audio = os.path.join(TTS_DIR, f"audio_short_{eid}.mp3")
            short_bgm = os.path.join(TTS_DIR, f"bgm_short_{eid}.mp3")
            gen_bg_music(short_bgm, 30)
            mix_audio(tts_segments[0], short_bgm, short_audio, duration_sec=30)

            final_short = os.path.join(VIDEOS_DIR, f"worldcup2026_episodi_{eid}_short.mp4")
            subprocess.run([
                ffmpeg(), "-y", "-i", short_vid, "-i", short_audio,
                "-c:v", "copy", "-c:a", "aac", "-b:a", "128k",
                "-shortest", final_short
            ], capture_output=True, timeout=300)
            print(f"  OK: {final_short}")

    shutil.rmtree(TTS_DIR, ignore_errors=True)
    print(f"\n{'=' * 55}")
    print(f"All videos ready in {VIDEOS_DIR}!")
    print(f"{'=' * 55}")

if __name__ == "__main__":
    main()
