"""
Download free FIFA World Cup 2026 images from Unsplash.
Uses only free-to-use (Unsplash License) images.
"""
import os
import requests
import time
import random

IMAGES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "images")
os.makedirs(IMAGES_DIR, exist_ok=True)

UNSPLASH_IMAGES = [
    ("stadium_aerial", "https://images.unsplash.com/photo-1431324155629-1a6deb1dec8d?w=1920"),
    ("football_action", "https://images.unsplash.com/photo-1459865264687-595d652de67e?w=1920"),
    ("trophy_celebration", "https://images.unsplash.com/photo-1511882150382-421056c89033?w=1920"),
    ("fans_cheering", "https://images.unsplash.com/photo-1530533718754-001d2668365a?w=1920"),
    ("player_kicking", "https://images.unsplash.com/photo-1574629810360-7efbbe195018?w=1920"),
    ("night_stadium", "https://images.unsplash.com/photo-1552674605-db6ffd4facb5?w=1920"),
    ("celebration_confetti", "https://images.unsplash.com/photo-1540747913346-19e32dc3e97e?w=1920"),
    ("soccer_ball", "https://images.unsplash.com/photo-1504639725590-34d0984388bd?w=1920"),
    ("training_session", "https://images.unsplash.com/photo-1522778119026-d647f0596c20?w=1920"),
    ("stadium_panorama", "https://images.unsplash.com/photo-1471506480208-91b3a4cc78be?w=1920"),
    ("fans_flag", "https://images.unsplash.com/photo-1495567720989-cebdbdd97913?w=1920"),
    ("golden_trophy", "https://images.unsplash.com/photo-1529900748604-07564a03e7a6?w=1920"),
    ("match_intensity", "https://images.unsplash.com/photo-1489944440615-453fc2b6a9a9?w=1920"),
    ("player_dribble", "https://images.unsplash.com/photo-1576458088443-04a19bb13da6?w=1920"),
    ("victory_pose", "https://images.unsplash.com/photo-1589487391730-58f20eb2c308?w=1920"),
    ("team_walk", "https://images.unsplash.com/photo-1517927033932-b3d18e61fb3a?w=1920"),
    ("stadium_floodlights", "https://images.unsplash.com/photo-1517466787929-bc90951d0974?w=1920"),
    ("goal_celebration", "https://images.unsplash.com/photo-1579952363873-27f3bade9f55?w=1920"),
    ("soccer_stadium", "https://images.unsplash.com/photo-1508098682722-e99c643e7f0b?w=1920"),
    ("team_celebration", "https://images.unsplash.com/photo-1461896836934-bd45ba8fcf9b?w=1920"),
]


def download():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    count = 0
    for name, url in UNSPLASH_IMAGES:
        fpath = os.path.join(IMAGES_DIR, f"{name}.jpg")
        if os.path.exists(fpath) and os.path.getsize(fpath) > 10000:
            continue
        try:
            r = requests.get(url, headers=headers, timeout=30)
            if r.status_code == 200:
                with open(fpath, "wb") as f:
                    f.write(r.content)
                print(f"  OK: {name} ({len(r.content)//1024} KB)")
                count += 1
            else:
                print(f"  FAIL: {name} (HTTP {r.status_code})")
        except Exception as e:
            print(f"  ERROR: {name} - {e}")
        time.sleep(random.uniform(0.3, 1.0))
    print(f"Downloaded {count} new images. Total: {len(os.listdir(IMAGES_DIR))} files.")


if __name__ == "__main__":
    download()
