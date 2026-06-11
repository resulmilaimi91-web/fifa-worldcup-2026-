import os, sys, json, random, subprocess, shutil, asyncio, argparse
from datetime import datetime, timezone, timedelta

BASE = os.path.dirname(os.path.dirname(__file__))
IMAGES_DIR = os.path.join(BASE, "images")
VIDEOS_DIR = os.path.join(BASE, "videos")
THUMBS_DIR = os.path.join(BASE, "thumbnails")
DATA_FILE = os.path.join(BASE, "data", "worldcup2026.json")
TTS_DIR = os.path.join(BASE, "tmp_tts")
os.makedirs(VIDEOS_DIR, exist_ok=True)
os.makedirs(THUMBS_DIR, exist_ok=True)
os.makedirs(TTS_DIR, exist_ok=True)

FPS = 24
W, H = 1920, 1080

def ffmpeg():
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return "ffmpeg"

def run_ff(cmd, timeout=120):
    r = subprocess.run(cmd, capture_output=True, timeout=timeout)
    if r.returncode != 0:
        err = r.stderr.decode("utf-8", errors="replace")[-500:]
        print(f"  FFmpeg ERROR (ret={r.returncode}): {err[:200]}")
    return r

def load_data():
    with open(DATA_FILE, encoding="utf-8") as f:
        return json.load(f)

def load_images():
    exts = {".jpg", ".jpeg", ".png"}
    return sorted([
        os.path.join(IMAGES_DIR, f) for f in os.listdir(IMAGES_DIR)
        if os.path.splitext(f)[1].lower() in exts
    ])

def gen_tts(text, output, voice="en-US-ChristopherNeural"):
    asyncio.run(__import__("edge_tts").Communicate(text, voice=voice).save(output))

def gen_bg_music(output, duration_sec):
    run_ff([
        ffmpeg(), "-y",
        "-f", "lavfi", "-i", f"anoisesrc=d={duration_sec}:c=pink:a=0.35",
        "-f", "lavfi", "-i", f"sine=frequency=110:duration={duration_sec}",
        "-f", "lavfi", "-i", f"sine=frequency=165:duration={duration_sec}",
        "-filter_complex",
        "[0:a]volume=0.06[a];"
        "[1:a]volume=0.02,afade=t=in:d=3[b];"
        "[2:a]volume=0.01,afade=t=in:d=5[c];"
        "[a][b]amix=inputs=2:duration=first[ab];"
        "[ab][c]amix=inputs=2:duration=first",
        "-ac", "1", "-ar", "22050", output
    ], timeout=120)

def prep_image(src, dst, w=W, h=H):
    run_ff([
        ffmpeg(), "-y", "-i", src,
        "-vf", f"scale={w}:{h}:force_original_aspect_ratio=1,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:color=black",
        "-qscale:v", "2", dst
    ], timeout=60)

def make_ken_burns_segment(images, output, duration_per_img=3.5):
    ff = ffmpeg()
    tmp = os.path.join(BASE, "tmp_seg")
    os.makedirs(tmp, exist_ok=True)

    resized = []
    for i, img in enumerate(images):
        dst = os.path.join(tmp, f"r_{i:03d}.jpg")
        prep_image(img, dst)
        resized.append(dst)

    segs = []
    for i, img in enumerate(resized):
        out = os.path.join(tmp, f"s_{i:03d}.mp4")
        dur = duration_per_img + 0.3
        cmd = [
            ff, "-y", "-loop", "1", "-i", img,
            "-vf", f"fps={FPS},zoompan=z=min(zoom+0.002,1.06):d={int(FPS*dur)}:s={W}x{H}:fps={FPS}",
            "-c:v", "libx264", "-t", str(dur),
            "-pix_fmt", "yuv420p", "-preset", "fast", "-crf", "23", out
        ]
        r = run_ff(cmd, timeout=120)
        if r.returncode == 0:
            segs.append(out)
        else:
            print(f"  WARN: zoompan failed for img {i}, skipping")

    if not segs:
        print(f"  ERROR: no valid segments created for {output}")
        return

    concat = os.path.join(tmp, "c.txt")
    with open(concat, "w") as f:
        for s in segs:
            f.write(f"file '{os.path.abspath(s)}'\n")
    run_ff([
        ff, "-y", "-f", "concat", "-safe", "0",
        "-i", concat, "-c", "copy", output
    ], timeout=300)
    shutil.rmtree(tmp, ignore_errors=True)

def add_lower_third(input_video, output_video, text_lines):
    ff = ffmpeg()
    if not os.path.exists(input_video):
        print(f"  WARN: {input_video} missing, skipping lower third")
        shutil.copy(input_video, output_video) if os.path.exists(input_video) else None
        return
    f = [f"drawbox=x=0:y=ih-80:w=iw:h=80:color=black@0.65:t=fill"]
    bold_font = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    reg_font = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    for i, line in enumerate(text_lines):
        escaped = line.replace(":", "\\:").replace("'", "\\\\'")
        fs = 36 if i == 0 else 26
        ft = bold_font if i == 0 else reg_font
        c = "gold" if i == 0 else "white"
        f.append(f"drawtext=text='{escaped}':fontfile={ft}:fontsize={fs}:fontcolor={c}:x=30:y={H-65+i*30}")
    r = run_ff([
        ff, "-y", "-i", input_video,
        "-vf", ",".join(f),
        "-c:v", "libx264", "-preset", "fast", "-crf", "23", output_video
    ], timeout=300)
    if r.returncode != 0 and os.path.exists(input_video):
        shutil.copy(input_video, output_video)

def add_title_card(input_video, output_video, title, subtitle=None):
    ff = ffmpeg()
    if not os.path.exists(input_video):
        print(f"  WARN: {input_video} missing, skipping title card")
        return
    f = [
        "drawbox=x=0:y=0:w=iw:h=ih:color=black@0.55:t=fill",
        f"drawtext=text='{title.replace(':', '\\:')}':fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:fontsize=56:fontcolor=gold:x=(w-text_w)/2:y=(h-text_h)/2-40:box=1:boxcolor=black@0.4:boxborderw=15"
    ]
    if subtitle:
        f.append(
            f"drawtext=text='{subtitle.replace(':', '\\:')}':fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf:fontsize=32:fontcolor=white:x=(w-text_w)/2:y=(h-text_h)/2+30"
        )
    r = run_ff([
        ff, "-y", "-i", input_video,
        "-vf", ",".join(f),
        "-c:v", "libx264", "-preset", "fast", "-crf", "23", output_video
    ], timeout=300)
    if (r.returncode != 0 or not os.path.exists(output_video)) and os.path.exists(input_video):
        shutil.copy(input_video, output_video)

def concat_videos(video_list, output):
    ff = ffmpeg()
    existing = [v for v in video_list if os.path.exists(v)]
    if not existing:
        print(f"  WARN: no videos to concat for {output}")
        return
    tmp = os.path.join(BASE, "tmp_cat")
    os.makedirs(tmp, exist_ok=True)
    cf = os.path.join(tmp, "c.txt")
    with open(cf, "w") as f:
        for v in existing:
            f.write(f"file '{os.path.abspath(v)}'\n")
    run_ff([
        ff, "-y", "-f", "concat", "-safe", "0",
        "-i", cf, "-c", "copy", output
    ], timeout=300)
    shutil.rmtree(tmp, ignore_errors=True)

def mix_audio(tts_file, bgm_file, output, duration=None):
    ff = ffmpeg()
    cmd = [
        ff, "-y", "-i", tts_file, "-i", bgm_file,
        "-filter_complex",
        "[1:a]volume=0.08[bgm];[0:a][bgm]amix=inputs=2:duration=first",
        "-ac", "1", "-ar", "22050"
    ]
    if duration:
        cmd += ["-t", str(duration)]
    cmd.append(output)
    run_ff(cmd, timeout=120)

def get_duration(file_path):
    if not os.path.exists(file_path):
        return 0
    ff = ffmpeg()
    r = subprocess.run([ff, "-i", file_path, "-f", "null", "-"],
                       capture_output=True, text=True, timeout=60)
    for line in r.stderr.split("\n"):
        if "Duration" in line:
            parts = line.strip().split(",")[0].split("Duration:")[-1].strip()
            h, m, s = parts.split(":")
            return int(h) * 3600 + int(m) * 60 + float(s)
    return 0

def make_thumbnail(images, output, title_text, episode_label):
    ff = ffmpeg()
    img = images[0] if images else os.path.join(IMAGES_DIR, os.listdir(IMAGES_DIR)[0])
    escaped = title_text.replace(":", "\\:").replace("'", "\\\\'")
    run_ff([
        ff, "-y", "-i", img,
        "-vf",
        f"scale=1280:720:force_original_aspect_ratio=1,pad=1280:720:(ow-iw)/2:(oh-ih)/2:color=black,"
        f"drawbox=x=0:y=0:w=iw:h=ih:color=black@0.35:t=fill,"
        f"drawtext=text='{escaped}':fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:"
        f"fontsize=42:fontcolor=gold:x=(w-text_w)/2:y=h*0.65:box=1:boxcolor=red@0.8:boxborderw=10,"
        f"drawtext=text='{episode_label}':fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf:"
        f"fontsize=28:fontcolor=white:x=(w-text_w)/2:y=h*0.8:box=1:boxcolor=black@0.6:boxborderw=8",
        "-qscale:v", "2", output
    ], timeout=60)

def generate_metadata(ep, eid):
    titles = [
        f"FIFA World Cup 2026 | {ep['title']}",
        f"{ep['title']} - FIFA World Cup 2026 Preview",
        f"FIFA World Cup 2026: {ep['subtitle']}",
    ]
    tags = ep.get("tags", []) + [
        "FIFA World Cup 2026", "World Cup 2026", "FIFA 2026",
        "World Cup Preview", "2026 World Cup", "Football 2026",
        "Soccer 2026", "World Cup Highlights", "FIFA",
        "World Cup Stadiums", "World Cup Players", "World Cup Fans",
        "USA 2026", "Mexico 2026", "Canada 2026",
        "World Cup Predictions", "Football Highlights"
    ]
    description = (
        f"{ep['title']} - FIFA World Cup 2026\n"
        f"{ep['subtitle']}\n\n"
        f"\u23f0 The biggest World Cup ever is here! 48 teams, 3 nations, 1 trophy.\n\n"
        f"\ud83d\udcf2 Follow for more FIFA World Cup 2026 content!\n"
        f"\ud83d\udd14 Subscribe and turn on notifications!\n\n"
        f"#FIFAWorldCup #WorldCup2026 #FIFA #Football #Soccer "
        + " ".join(f"#{t}" for t in tags[:10])
    )
    return titles, description, tags

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("count", nargs="?", default="5")
    args = parser.parse_args()
    count = min(int(args.count), 5)

    print("=" * 55)
    print("FIFA World Cup 2026 - Complete Auto Generator")
    print("Viral-optimized | Inspired by FIFA Preview Series")
    print("=" * 55)

    data = load_data()
    episodes = data["episodes"][:count]
    images = load_images()
    print(f"Images: {len(images)}")
    if len(images) < 5:
        print("Not enough images. Run download_images.py first.")
        return

    manifest = []

    for ep in episodes:
        eid = ep["id"]
        title = ep["title"]
        subtitle = ep["subtitle"]
        scripts = ep["script"]
        ep_name = f"Episodi {eid}"

        print(f"\n--- {ep_name}: {title} ---")
        random.seed(ep_name)
        random.shuffle(images)

        video_segments = []
        total_imgs = 0
        for seg_idx, script_text in enumerate(scripts):
            imgs_per = max(4, min(8, len(images) // len(scripts)))
            start = seg_idx * imgs_per
            seg_imgs = images[start:start+imgs_per]
            if not seg_imgs:
                seg_imgs = images[:4]
            print(f"  Seg {seg_idx+1}: {len(seg_imgs)} images")

            raw = os.path.join(TTS_DIR, f"raw_{eid}_{seg_idx}.mp4")
            make_ken_burns_segment(seg_imgs, raw)

            styled = os.path.join(TTS_DIR, f"sty_{eid}_{seg_idx}.mp4")
            if os.path.exists(raw):
                add_lower_third(raw, styled, [title, f"{ep_name} | World Cup 2026"])

            titled = os.path.join(TTS_DIR, f"til_{eid}_{seg_idx}.mp4")
            used = styled if os.path.exists(styled) else raw
            add_title_card(used, titled, title, subtitle)

            final_seg = titled if os.path.exists(titled) else (styled if os.path.exists(styled) else raw)
            if os.path.exists(final_seg):
                video_segments.append(final_seg)
            total_imgs += len(seg_imgs)

        concat_vid = os.path.join(TTS_DIR, f"cat_{eid}.mp4")
        concat_videos(video_segments, concat_vid)
        vid_dur = get_duration(concat_vid)
        print(f"  Duration: {vid_dur:.0f}s ({vid_dur/60:.1f} min)")

        # Generate TTS
        tts_segs = []
        for seg_idx, script_text in enumerate(scripts):
            ttf = os.path.join(TTS_DIR, f"tts_{eid}_{seg_idx}.mp3")
            try:
                gen_tts(script_text, ttf)
                tts_segs.append(ttf)
            except Exception as e:
                print(f"  TTS error: {e}")

        if tts_segs:
            # Concat TTS
            tts_all = os.path.join(TTS_DIR, f"tts_all_{eid}.mp3")
            cf = os.path.join(TTS_DIR, f"tts_concat_{eid}.txt")
            with open(cf, "w") as f:
                for ts in tts_segs:
                    if os.path.exists(ts):
                        f.write(f"file '{os.path.abspath(ts)}'\n")
            run_ff([ffmpeg(), "-y", "-f", "concat", "-safe", "0",
                   "-i", cf, "-c", "copy", tts_all], timeout=120)

            bgm = os.path.join(TTS_DIR, f"bgm_{eid}.mp3")
            gen_bg_music(bgm, max(vid_dur, 30))

            mixed = os.path.join(TTS_DIR, f"aud_{eid}.mp3")
            mix_audio(tts_all, bgm, mixed, vid_dur)

            final_long = os.path.join(VIDEOS_DIR, f"worldcup2026_episodi_{eid}.mp4")
            run_ff([
                ffmpeg(), "-y", "-i", concat_vid, "-i", mixed,
                "-c:v", "copy", "-c:a", "aac", "-b:a", "128k",
                "-shortest", final_long
            ], timeout=300)
            print(f"  [LONG] {final_long}")

        # Short
        short_vid = os.path.join(TTS_DIR, f"short_{eid}.mp4")
        if video_segments and os.path.exists(video_segments[0]):
            shutil.copy(video_segments[0], short_vid)
        else:
            make_ken_burns_segment(images[:6], short_vid, 2.5)

        if tts_segs and os.path.exists(short_vid):
            sa = os.path.join(TTS_DIR, f"aud_s_{eid}.mp3")
            bgm_s = os.path.join(TTS_DIR, f"bgm_s_{eid}.mp3")
            gen_bg_music(bgm_s, 30)
            mix_audio(tts_segs[0], bgm_s, sa, 30)

            final_short = os.path.join(VIDEOS_DIR, f"worldcup2026_episodi_{eid}_short.mp4")
            run_ff([
                ffmpeg(), "-y", "-i", short_vid, "-i", sa,
                "-c:v", "copy", "-c:a", "aac", "-b:a", "128k",
                "-shortest", final_short
            ], timeout=300)
            print(f"  [SHORT] {final_short}")

        # Generate metadata
        titles, desc, tags = generate_metadata(ep, eid)
        meta = {
            "episode": eid,
            "title_options": titles,
            "description": desc,
            "tags": tags,
            "best_post_time_et": "20:00",
            "best_post_time_pt": "17:00",
        }
        meta_file = os.path.join(VIDEOS_DIR, f"worldcup2026_episodi_{eid}_metadata.json")
        with open(meta_file, "w") as f:
            json.dump(meta, f, indent=2)
        print(f"  [META] {meta_file}")

        manifest.append({
            "episode": eid,
            "title": title,
            "video": f"worldcup2026_episodi_{eid}.mp4",
            "short": f"worldcup2026_episodi_{eid}_short.mp4",
            "thumbnail": f"worldcup2026_ep{eid}_thumb.jpg",
            "metadata": f"worldcup2026_episodi_{eid}_metadata.json",
            "best_post_time_et": "20:00",
            "best_post_time_pt": "17:00"
        })

    # Save release manifest
    now = datetime.now(timezone.utc)
    release = {
        "generated_at": now.isoformat(),
        "generated_at_et": (now - timedelta(hours=4)).strftime("%Y-%m-%d %H:%M ET"),
        "episodes": manifest,
        "posting_schedule": {
            "monday_friday": "20:00 ET / 17:00 PT",
            "weekend": "12:00 ET / 09:00 PT",
            "timezone": "US Prime Time"
        }
    }
    with open(os.path.join(VIDEOS_DIR, "release_manifest.json"), "w") as f:
        json.dump(release, f, indent=2)

    shutil.rmtree(TTS_DIR, ignore_errors=True)
    print(f"\n{'=' * 55}")
    print(f"ALL COMPLETE!")
    print(f"Videos: {VIDEOS_DIR}")
    print(f"Post schedule: US Prime Time (20:00 ET / 17:00 PT)")
    print(f"{'=' * 55}")

if __name__ == "__main__":
    main()
