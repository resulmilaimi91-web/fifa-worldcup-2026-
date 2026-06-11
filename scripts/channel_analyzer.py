"""
FIFA Channel Auto-Analyzer
Downloads latest FIFA World Cup 2026 videos and extracts style patterns
"""
import subprocess, json, os, re, sys

BASE = os.path.dirname(os.path.dirname(__file__))
ANALYSIS_DIR = os.path.join(BASE, "channel_data")
os.makedirs(ANALYSIS_DIR, exist_ok=True)

def get_ffmpeg():
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return "ffmpeg"

def analyze_video(video_path):
    """Extract detailed metrics from a video"""
    ff = get_ffmpeg()
    info = {}

    # Get duration
    result = subprocess.run([ff, "-i", video_path, "-f", "null", "-"],
                            capture_output=True, text=True, timeout=120)
    for line in result.stderr.split("\n"):
        if "Duration" in line:
            parts = line.strip().split(",")[0].split("Duration:")[-1].strip()
            h, m, s = parts.split(":")
            info["duration"] = int(h) * 3600 + int(m) * 60 + float(s)

    # Scene detection
    result2 = subprocess.run([
        ff, "-i", video_path,
        "-filter:v", "select=gt(scene\\,0.3),showinfo",
        "-f", "null", "-"
    ], capture_output=True, text=True, timeout=300)

    scenes = []
    for line in result2.stderr.split("\n"):
        if "pts_time:" in line:
            parts = line.split()
            for p in parts:
                if p.startswith("pts_time:"):
                    try:
                        scenes.append(float(p.split(":")[1]))
                    except:
                        pass

    if len(scenes) > 1:
        gaps = [scenes[i] - scenes[i-1] for i in range(1, len(scenes))]
        gaps = [g for g in gaps if 0.5 < g < 120]
        info["num_shots"] = len(gaps)
        info["avg_shot"] = sum(gaps) / len(gaps) if gaps else 0
        info["quick_cuts"] = len([g for g in gaps if g < 3])
        info["medium_cuts"] = len([g for g in gaps if 3 <= g < 8])
        info["long_cuts"] = len([g for g in gaps if g >= 8])

    return info

def extract_fifa_channel_data():
    """Get latest FIFA channel video info using yt-dlp"""
    # Analyze the video we already downloaded
    video_path = r"C:\Users\User\Downloads\fifa_channel_ref.mp4"
    if os.path.exists(video_path):
        print(f"Analyzing: {video_path}")
        info = analyze_video(video_path)
        with open(os.path.join(ANALYSIS_DIR, "fifa_style.json"), "w") as f:
            json.dump(info, f, indent=2)
        print(f"Style data saved.")
        return info
    else:
        print("Reference video not found")
        return None

if __name__ == "__main__":
    data = extract_fifa_channel_data()
    if data:
        print(json.dumps(data, indent=2))
