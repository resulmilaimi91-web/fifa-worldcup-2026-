# FIFA World Cup 2026 - YouTube Content Generator

Automatizim per krijimin e videove te FIFA World Cup 2026 per YouTube.

## Si punon

1. **Shkarkon imazhe falas** nga Unsplash (te lira per cdo perdorim)
2. **Krijon slideshow** me efekt Ken Burns (zoom in)
3. **Gjeneron** video te gjata (~3 min) dhe Shorts (~30-60 sek)
4. **Nxjerr korniza** nga video reference te FIFA per inspirim

## Instalim

```bash
pip install -r requirements.txt
```

## Perdorim

```bash
# Shkarko imazhe
python scripts/download_images.py

# Gjenero video
python scripts/generate_videos.py

# Gjenero vetem nje numer episodash
python scripts/generate_videos.py --episodes 3
```

## Struktura

```
worldcup2026/
├── images/              # Imazhet e shkarkuara
├── videos/              # Videot e gjeneruara
├── reference_frames/    # Korniza nga video reference
├── scripts/
│   ├── download_images.py
│   └── generate_videos.py
├── .github/workflows/   # GitHub Actions automation
└── requirements.txt
```

## Episodet

| Episodi | Titulli | Perfshin |
|---------|---------|----------|
| 1 | FIFA World Cup 2026 - Kupa e Botes | Hyrje ne Boteror |
| 2 | Stadiumet e Boterorit 2026 | USA, Mexico, Kanada |
| 3 | Yjet e Boterorit 2026 | Lojtaret me te mire |
| 4 | Tifozet e Boterorit | Pasioni i futbollit |
| 5 | Momente te paharrueshme | Aksioni me i mire |

## License

Imazhet jane nga Unsplash (Unsplash License - falas per perdorim komercial dhe jokomercial).
