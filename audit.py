from pathlib import Path
from collections import Counter
from PIL import Image
import random, re, statistics

ROOT = Path.home() / "JARVIS-BOX" / "dataset"
NAMA = {0: "Fire", 1: "Smoke"}
EXT = {".jpg", ".jpeg", ".png"}

def dasar(nama):
    # Roboflow: "asli_jpg.rf.<hash>.jpg" -> kelompokkan salinan augmentasi
    return re.split(r"\.rf\.", nama)[0]

def baca_label(lbl):
    out = []
    if not lbl.exists():
        return out
    for baris in lbl.read_text().strip().splitlines():
        p = baris.split()
        if len(p) < 5:
            continue
        c = int(float(p[0]))
        if len(p) == 5:
            w, h = float(p[3]), float(p[4])
        else:  # format poligon -> ambil bounding box
            xs = [float(v) for v in p[1::2]]
            ys = [float(v) for v in p[2::2]]
            w, h = max(xs) - min(xs), max(ys) - min(ys)
        out.append((c, w * h))
    return out

basis_per_split = {}
for split in ["train", "valid", "test"]:
    img_dir = ROOT / split / "images"
    if not img_dir.exists():
        print(f"\n[{split}] folder tidak ada")
        continue
    imgs = [p for p in img_dir.iterdir() if p.suffix.lower() in EXT]
    kelas, luas = Counter(), []
    tanpa_label = 0
    jenis = Counter()
    for p in imgs:
        objs = baca_label(ROOT / split / "labels" / (p.stem + ".txt"))
        if not objs:
            tanpa_label += 1
            continue
        ada = {c for c, _ in objs}
        jenis["keduanya" if len(ada) == 2 else NAMA.get(next(iter(ada)), "?") + " saja"] += 1
        for c, a in objs:
            kelas[c] += 1
            luas.append((c, a))
    basis = {dasar(p.name) for p in imgs}
    basis_per_split[split] = basis
    sampel = random.sample(imgs, min(200, len(imgs)))
    ukuran = Counter(Image.open(p).size for p in sampel)

    print(f"\n===== {split.upper()} =====")
    print(f"Gambar: {len(imgs)} | gambar unik (tanpa salinan augmentasi): {len(basis)}"
          f" | rata-rata {len(imgs)/max(len(basis),1):.1f} salinan per gambar asli")
    print(f"Tanpa label (negatif): {tanpa_label} ({tanpa_label/max(len(imgs),1):.1%})")
    print("Isi gambar berlabel:", dict(jenis))
    print("Jumlah kotak per kelas:", {NAMA.get(k, k): v for k, v in kelas.items()})
    print("Ukuran gambar (sampel 200):", ukuran.most_common(3))
    for c in sorted(kelas):
        a = [x for k, x in luas if k == c]
        kecil = sum(1 for x in a if x < 0.01) / len(a)
        besar = sum(1 for x in a if x > 0.25) / len(a)
        print(f"  {NAMA.get(c, c)}: median luas kotak {statistics.median(a):.1%} dari gambar,"
              f" kotak kecil (<1%) {kecil:.0%}, kotak besar (>25%) {besar:.0%}")

sp = list(basis_per_split)
for i in range(len(sp)):
    for j in range(i + 1, len(sp)):
        irisan = basis_per_split[sp[i]] & basis_per_split[sp[j]]
        print(f"\nGambar asli yang sama di {sp[i]} dan {sp[j]}: {len(irisan)}")
