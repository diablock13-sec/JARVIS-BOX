import argparse, random, sys
from pathlib import Path
import cv2

ap = argparse.ArgumentParser()
ap.add_argument("--dir", default=str(Path.home() / "Downloads"))
ap.add_argument("--n", type=int, default=61)
ap.add_argument("--val", type=int, default=12)
ap.add_argument("--tulis", action="store_true")
a = ap.parse_args()

EKS = {".jpg", ".jpeg", ".png", ".webp", ".jfif", ".bmp"}
fs = sorted((p for p in Path(a.dir).iterdir() if p.suffix.lower() in EKS),
            key=lambda p: p.stat().st_mtime, reverse=True)[:a.n]
print(f"{len(fs)} gambar terbaru di {a.dir}:")
for p in fs:
    print(f"  {p.name}  {p.stat().st_size // 1024} KB")
if len(fs) <= a.val:
    sys.exit("Gambar terlalu sedikit.")

random.seed(7)
acak = fs[:]; random.shuffle(acak)
val, train = acak[:a.val], acak[a.val:]
print(f"\nRencana: train {len(train)}, val {len(val)} (acak, tidak ada gambar di dua sisi).")
if not a.tulis:
    print("Pratinjau saja. Tambahkan --tulis untuk menyalin.")
    sys.exit()

for nama, daftar in (("train", train), ("val", val)):
    d = Path("sumber_layar", nama); d.mkdir(parents=True, exist_ok=True)
    ada = len(list(d.glob("*.jpg")))
    for i, p in enumerate(daftar, ada + 1):
        im = cv2.imread(str(p))
        if im is None:
            print("gagal baca", p.name); continue
        cv2.imwrite(str(d / f"src_{i:02d}.jpg"), im, [cv2.IMWRITE_JPEG_QUALITY, 95])
    print(nama, len(list(d.glob("*.jpg"))), "file")
