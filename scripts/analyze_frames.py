from PIL import Image
import os

d = r"D:\ANDROID\opencode\worldcup2026\channel_analysis"
for f in sorted(os.listdir(d)):
    if not f.endswith(".jpg"):
        continue
    fp = os.path.join(d, f)
    img = Image.open(fp).convert("RGB")
    w, h = img.size

    bottom = img.crop((0, int(h * 0.85), w, h))
    bp = list(bottom.getdata())
    avg_b = tuple(sum(c) // len(bp) for c in zip(*bp))
    b_bright = sum(avg_b) // 3

    left_third = img.crop((0, int(h * 0.3), int(w * 0.3), int(h * 0.7)))
    lp = list(left_third.getdata())
    avg_l = tuple(sum(c) // len(lp) for c in zip(*lp))
    l_bright = sum(avg_l) // 3

    result = "normal"
    if b_bright < 50:
        result = "dark_bar-bottom"
    elif b_bright > 200:
        result = "light_bar-bottom"
    if l_bright < 50:
        result += "+left_text"

    print(f"{f}: bottom={b_bright}, left={l_bright}, style={result}")
    img.close()
