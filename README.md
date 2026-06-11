# FIFA World Cup 2026 - YouTube Content Generator 🤖🎬

Automatizim i plotë për krijimin e videove të FIFA World Cup 2026, i stilit **FIFA Preview Series**.

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🎤 **TTS Narration** | Zë shqip (`sq-AL-IlirNeural`) - flet për çdo episod |
| 🎵 **Background Music** | Ambient original (pa copyright), i gjeneruar nga FFmpeg |
| 🎬 **Ken Burns Zoom** | Zoom i butë në çdo imazh si dokumentar |
| 📝 **FIFA-style overlays** | Shirit i zi poshtë + tekst (emra lojtarësh/skuadrash) |
| ⚡ **Fast cuts** | Çdo imazh 3.5 sekonda (si FIFA Preview Series) |
| 📊 **Multi-segment** | Çdo episod ka 3 segmente me narracion të ndarë |
| 🤖 **GitHub Actions** | Kliko "Run workflow" dhe merr videot gati |
| 📱 **Long + Short** | Gjeneron automatikisht version të gjatë dhe short |

## 🚀 Përdorimi

### Lokalisht
```bash
pip install -r requirements.txt
python scripts/download_images.py
python scripts/generate_videos.py 5   # 5 episode
```

### Në GitHub
1. Shko te **Actions** → **FIFA World Cup 2026 - Full Video Generator**
2. Kliko **Run workflow** → zgjidh numrin e episodeve → **Run**
3. Pas ~5 min, shkarko **Artifacts** → `worldcup2026-videos-complete.zip`

## 📁 Struktura

```
├── .github/workflows/generate.yml   ← GitHub Actions
├── scripts/
│   ├── download_images.py           ← Shkarkon imazhe falas
│   └── generate_videos.py           ← Gjenerator i plotë
├── data/worldcup2026.json           ← Të dhënat e episodeve
├── images/                          ← Imazhet
├── videos/                          ← Videot e gatshme
├── channel_analysis/                ← Analizë e kanalit FIFA
└── requirements.txt
```

## 📺 Episodet

| # | Titulli | Përshkrimi |
|---|---------|------------|
| 1 | Kupa e Botës 2026 | Botërori më i madh në histori |
| 2 | Stadiumet e Botërorit 2026 | 16 tempuj të futbollit |
| 3 | Yjet e Botërorit 2026 | Lojtarët më të mirë në botë |
| 4 | Tifozët e Botërorit | Pasioni që bashkon botën |
| 5 | Fantastike 2026 | Momentet më të mira |

## 🎯 Stili (i bazuar në FIFA Preview Series)

- **Shot duration**: 3.5s (analizuar: avg 4.4s, 50% cuts <3s)
- **Lower third**: Shirit i zi 80px + tekst ari/bardhë
- **Narration**: TTS në shqip me muzikë ambient
- **Ken Burns**: 6% zoom gjatë çdo shot-i

## 📝 License

Imazhet: Unsplash License (falas për përdorim komercial)
Kodi: Open source
