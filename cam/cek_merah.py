#!/usr/bin/env python3
"""Cari adegan yang didominasi warna merah/oranye di satu sesi foto.

Pakai (dari ~/JARVIS-BOX):
    python cam/cek_merah.py camA_terang
    python cam/cek_merah.py camA_terang --ambang 0.08
    python cam/cek_merah.py camA_terang --ambang 0.08 --pindah
"""
import argparse
import re
import shutil
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

POLA = re.compile(r"adegan(\d+)_f(\d+)\.jpg$")


def kelompok(folder):
    d = {}
    for p in sorted(folder.glob("adegan*_f*.jpg")):
        m = POLA.match(p.name)
        if m:
            d.setdefault(int(m.group(1)), []).append(p)
    return d


def skor_merah(path):
    """Bagian piksel yang jelas merah/oranye (bukan cokelat kayu atau kulit)."""
    a = np.asarray(Image.open(path).convert("RGB")).astype(int)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    merah = (r > 150) & ((r - np.maximum(g, b)) > 80)
    return float(merah.mean())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("sesi")
    ap.add_argument("--ambang", type=float, default=0.08,
                    help="batas bagian piksel merah (0.08 = 8 persen)")
    ap.add_argument("--pindah", action="store_true")
    a = ap.parse_args()

    root = Path.home() / "JARVIS-BOX" / "foto_cam"
    folder = root / a.sesi
    adegan = kelompok(folder)
    if not adegan:
        raise SystemExit(f"Tidak ada foto adeganNN_fK.jpg di {folder}")

    hasil = []
    for n, files in adegan.items():
        s = float(np.mean([skor_merah(p) for p in files]))
        hasil.append((s, n, len(files)))
    hasil.sort(reverse=True)

    print(f"{len(adegan)} adegan, {sum(len(v) for v in adegan.values())} foto di {folder}")
    print("\nAdegan paling merah (skor = rata-rata bagian piksel merah/oranye):")
    for s, n, k in hasil[:20]:
        tanda = "  <-- di atas ambang" if s >= a.ambang else ""
        print(f"  adegan{n:02d}  {s:6.1%}  ({k} frame){tanda}")
    di_atas = [n for s, n, _ in hasil if s >= a.ambang]
    print(f"\nDi atas ambang {a.ambang:.0%}: {len(di_atas)} adegan")

    top = [n for _, n, _ in hasil[:16]]
    w, h = 240, 180
    kolom = 4
    baris = (len(top) + kolom - 1) // kolom
    kanvas = Image.new("RGB", (kolom * w, baris * h), "white")
    for i, n in enumerate(top):
        im = Image.open(adegan[n][0]).convert("RGB").resize((w, h))
        d = ImageDraw.Draw(im)
        d.rectangle([0, 0, 110, 14], fill="black")
        d.text((3, 1), f"adegan{n:02d}", fill="white")
        kanvas.paste(im, ((i % kolom) * w, (i // kolom) * h))
    out = Path.home() / "JARVIS-BOX" / "cek_merah.jpg"
    kanvas.save(out, quality=90)
    print(f"Gambar ringkasan: {out}")

    if a.pindah:
        if not di_atas:
            print("Tidak ada yang dipindah.")
            return
        print(f"\nAkan memindahkan adegan {sorted(di_atas)} ke camA_pemicu.")
        if input("Ketik 'ya' untuk lanjut: ").strip().lower() != "ya":
            print("Dibatalkan.")
            return
        tujuan = root / "camA_pemicu"
        tujuan.mkdir(parents=True, exist_ok=True)
        ada = kelompok(tujuan)
        baru = max(ada, default=0)
        for n in sorted(di_atas):
            baru += 1
            for p in adegan[n]:
                k = POLA.match(p.name).group(2)
                shutil.move(str(p), str(tujuan / f"adegan{baru:02d}_f{k}.jpg"))
            print(f"  adegan{n:02d} -> camA_pemicu/adegan{baru:02d}")
        print("Selesai. Nomor adegan di sesi asal tidak dirapikan (itu tidak masalah).")


if __name__ == "__main__":
    main()
