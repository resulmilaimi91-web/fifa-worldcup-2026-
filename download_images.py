import os
import requests
import json
import time
import random

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "images")
os.makedirs(OUTPUT_DIR, exist_ok=True)

unsplash_free_photos = [
    {
        "id": "FAZIDvA5jag",
        "url": "https://images.unsplash.com/photo-1747913880786-1b8f5d7f4c7a?w=1920",
        "title": "Stadium full of cheering fans",
        "tags": ["stadium", "fans", "world-cup", "football"]
    },
    {
        "id": "onMIbTpAww4",
        "url": "https://images.unsplash.com/photo-1747599416074-6f4c7a2f8d5a?w=1920",
        "title": "Soccer player celebrates on field",
        "tags": ["player", "celebration", "soccer", "goal"]
    },
    {
        "id": "iS6De9mUkek",
        "url": "https://images.unsplash.com/photo-1748456734799-45b9f8f7e2c1?w=1920",
        "title": "Soccer players on field at dusk",
        "tags": ["players", "stadium", "dusk", "match"]
    },
    {
        "id": "ZOJg4CtbKwk",
        "url": "https://images.unsplash.com/photo-1747913880781-8b5f8d7f4c7a?w=1920",
        "title": "Soccer players warming up",
        "tags": ["warmup", "training", "stadium", "team"]
    },
]

pexels_free_videos = [
    {
        "id": "soccer_match_01",
        "url": "https://www.pexels.com/download/video/8542010/",
        "title": "Soccer Match Highlights",
        "tags": ["match", "soccer", "highlights"]
    },
    {
        "id": "worldcup_fans_01",
        "url": "https://www.pexels.com/download/video/8542011/",
        "title": "Football Fans Celebrating",
        "tags": ["fans", "celebration", "football"]
    },
]

image_urls = [
    "https://images.unsplash.com/photo-1431324155629-1a6deb1dec8d?w=1920&q=80",
    "https://images.unsplash.com/photo-1459865264687-595d652de67e?w=1920&q=80",
    "https://images.unsplash.com/photo-1508098682722-e99c643e7f0b?w=1920&q=80",
    "https://images.unsplash.com/photo-1511882150382-421056c89033?w=1920&q=80",
    "https://images.unsplash.com/photo-1530533718754-001d2668365a?w=1920&q=80",
    "https://images.unsplash.com/photo-1574629810360-7efbbe195018?w=1920&q=80",
    "https://images.unsplash.com/photo-1552674605-db6ffd4facb5?w=1920&q=80",
    "https://images.unsplash.com/photo-1461896836934-bd45ba8fcf9b?w=1920&q=80",
    "https://images.unsplash.com/photo-1517466787929-bc90951d0974?w=1920&q=80",
    "https://images.unsplash.com/photo-1579952363873-27f3bade9f55?w=1920&q=80",
    "https://images.unsplash.com/photo-1504639725590-34d0984388bd?w=1920&q=80",
    "https://images.unsplash.com/photo-1522778119026-d647f0596c20?w=1920&q=80",
    "https://images.unsplash.com/photo-1560272564-c83b4b0c6c9d?w=1920&q=80",
    "https://images.unsplash.com/photo-1522778119026-d647f0596c20?w=1920&q=80",
    "https://images.unsplash.com/photo-1471506480208-91b3a4cc78be?w=1920&q=80",
    "https://images.unsplash.com/photo-1495567720989-cebdbdd97913?w=1920&q=80",
    "https://images.unsplash.com/photo-1529900748604-07564a03e7a6?w=1920&q=80",
    "https://images.unsplash.com/photo-1489944440615-453fc2b6a9a9?w=1920&q=80",
    "https://images.unsplash.com/photo-1576458088443-04a19bb13da6?w=1920&q=80",
    "https://images.unsplash.com/photo-1574629810360-7efbbe195018?w=1920&q=80",
    "https://images.unsplash.com/photo-1589487391730-58f20eb2c308?w=1920&q=80",
    "https://images.unsplash.com/photo-1517927033932-b3d18e61fb3a?w=1920&q=80",
    "https://images.unsplash.com/photo-1459865264687-595d652de67e?w=1920&q=80",
    "https://images.unsplash.com/photo-1461896836934-bd45ba8fcf9b?w=1920&q=80",
    "https://images.unsplash.com/photo-1579952363873-27f3bade9f55?w=1920&q=80",
    "https://images.unsplash.com/photo-1508098682722-e99c643e7f0b?w=1920&q=80",
    "https://images.unsplash.com/photo-1489944440615-453fc2b6a9a9?w=1920&q=80",
    "https://images.unsplash.com/photo-1517466787929-bc90951d0974?w=1920&q=80",
    "https://images.unsplash.com/photo-1504639725590-34d0984388bd?w=1920&q=80",
    "https://images.unsplash.com/photo-1574629810360-7efbbe195018?w=1920&q=80",
]

names = [
    "stadium_aerial", "football_action", "stadium_crowd", "trophy_celebration",
    "fans_cheering", "player_kicking", "night_stadium", "worldcup_trophy",
    "team_huddle", "celebration_confetti", "soccer_ball", "training_session",
    "goal_celebration", "stadium_panorama", "fans_flag", "golden_trophy",
    "match_intensity", "stadium_floodlights", "player_dribble", "corner_kick",
    "victory_pose", "team_walk", "action_slowmo", "stadium_empty",
    "free_kick", "crowd_wave", "penalty_shootout", "coaching_session", "champion_glory", "fan_paint"
]

def download_image(url, index, name):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        r = requests.get(url, headers=headers, timeout=30)
        if r.status_code == 200:
            ext = ".jpg"
            filename = f"{index:02d}_{name}{ext}"
            filepath = os.path.join(OUTPUT_DIR, filename)
            with open(filepath, "wb") as f:
                f.write(r.content)
            print(f"  [OK] {filename} ({len(r.content)//1024} KB)")
            return filepath
        else:
            print(f"  [FAIL] {url} - HTTP {r.status_code}")
            return None
    except Exception as e:
        print(f"  [ERROR] {url} - {e}")
        return None

print("=" * 60)
print("Shkarkimi i imazheve te lira per FIFA World Cup 2026")
print("=" * 60)

downloaded = []
for i, url in enumerate(image_urls):
    name = names[i] if i < len(names) else f"image_{i}"
    print(f"\n[{i+1}/{len(image_urls)}] Duke shkarkuar: {name}")
    result = download_image(url, i+1, name)
    if result:
        downloaded.append(result)
    time.sleep(random.uniform(0.5, 1.5))

print(f"\n{'=' * 60}")
print(f"Te shkarkuar: {len(downloaded)} nga {len(image_urls)} imazhe")
print(f"Folder: {OUTPUT_DIR}")
print(f"{'=' * 60}")
