import sys, os, random
sys.path.insert(0, "scripts")
from generate_videos import SERIES, load_images, create_slideshow_ffmpeg, VIDEOS_DIR

imgs = load_images()
remaining = SERIES[3:5]
for ep in remaining:
    random.seed(ep["episode"])
    random.shuffle(imgs)
    sel = imgs[:12]
    print(f'{ep["episode"]}: {ep["title"]}')
    out_l = os.path.join(VIDEOS_DIR, f'worldcup2026_{ep["episode"].lower().replace(" ", "_")}.mp4')
    create_slideshow_ffmpeg(sel, out_l, img_dur=15.0)
    print("  Long: OK")
    short_sel = sel[:6]
    out_s = os.path.join(VIDEOS_DIR, f'worldcup2026_{ep["episode"].lower().replace(" ", "_")}_short.mp4')
    create_slideshow_ffmpeg(short_sel, out_s, img_dur=10.0)
    print("  Short: OK")
print("Done!")
