import os, sys, random, argparse, subprocess, shutil

BASE = os.path.dirname(os.path.dirname(__file__))
IMAGES_DIR = os.path.join(BASE, "images")
VIDEOS_DIR = os.path.join(BASE, "videos")
os.makedirs(VIDEOS_DIR, exist_ok=True)

SERIES = [
    ("FIFA World Cup 2026 - Kupa e Botes", "Episodi 1"),
    ("Stadiumet e Boterorit 2026", "Episodi 2"),
    ("Yjet e Boterorit 2026", "Episodi 3"),
    ("Tifozet e Boterorit - Pasioni i futbollit", "Episodi 4"),
    ("Momente te paharrueshme FIFA 2026", "Episodi 5"),
]

def ffmpeg():
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return "ffmpeg"

def prep_image(src, dst, w=1920, h=1080):
    subprocess.run(
        [ffmpeg(), "-y", "-i", src,
         "-vf", f"scale={w}:{h}:force_original_aspect_ratio=1,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:color=black",
         "-qscale:v", "2", dst],
        capture_output=True, timeout=60)

def make_slideshow(images, output, sec_per_img=15.0):
    ff = ffmpeg()
    tmp = os.path.join(BASE, "tmp_ss")
    os.makedirs(tmp, exist_ok=True)
    resized = []
    for i, img in enumerate(images):
        dst = os.path.join(tmp, f"r_{i:03d}.jpg")
        prep_image(img, dst)
        resized.append(dst)

    files = []
    for i, img in enumerate(resized):
        out = os.path.join(tmp, f"s_{i:03d}.mp4")
        cmd = [ff, "-y", "-loop", "1", "-i", img,
               "-c:v", "libx264", "-t", str(sec_per_img + 0.3),
               "-pix_fmt", "yuv420p", "-preset", "fast", "-crf", "23",
               "-vf", "fps=24", out]
        subprocess.run(cmd, capture_output=True, timeout=120)
        files.append(out)

    concat = os.path.join(tmp, "c.txt")
    with open(concat, "w") as f:
        for v in files:
            f.write(f"file '{os.path.abspath(v)}'\n")

    subprocess.run([ff, "-y", "-f", "concat", "-safe", "0",
                    "-i", concat, "-c", "copy", output],
                   capture_output=True, timeout=300)
    shutil.rmtree(tmp, ignore_errors=True)

def load_images():
    exts = {'.jpg', '.jpeg', '.png'}
    return sorted([
        os.path.join(IMAGES_DIR, f) for f in os.listdir(IMAGES_DIR)
        if os.path.splitext(f)[1].lower() in exts
    ])

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("episodes", nargs="?", default="5")
    args = parser.parse_args()
    count = min(int(args.episodes), 5)

    images = load_images()
    print(f"Images: {len(images)}")
    if len(images) < 3:
        print("Not enough images. Run scripts/download_images.py first.")
        return

    for title, episode in SERIES[:count]:
        random.seed(episode)
        random.shuffle(images)
        sel = images[:12]
        print(f"\n{episode}: {title}")

        # Long
        name = f"worldcup2026_{episode.lower().replace(' ', '_')}.mp4"
        make_slideshow(sel, os.path.join(VIDEOS_DIR, name), sec_per_img=15.0)
        print(f"  OK: {name}")

        # Short
        name_s = f"worldcup2026_{episode.lower().replace(' ', '_')}_short.mp4"
        make_slideshow(sel[:6], os.path.join(VIDEOS_DIR, name_s), sec_per_img=10.0)
        print(f"  OK: {name_s}")

    print(f"\nDone! Files in {VIDEOS_DIR}")

if __name__ == "__main__":
    main()
