#!/usr/bin/env python3
"""Kelompokkan adegan berurutan yang tampak sama (kamera tidak dipindah).

Pakai (dari ~/JARVIS-BOX):
    python cam/kelompok_adegan.py camA_terang
    python cam/kelompok_adegan.py camA_terang --ambang 0.22

Hasil:
- daftar jarak antar adegan berurutan di layar
- foto_cam/<sesi>/kelompok.txt  (grup01: adegan01 adegan02 ...)
- ~/JARVIS-BOX/kelompok_<sesi>.jpg (adegan pertama tiap grup, untuk dilihat)
Tidak ada foto yang dipindah atau dihapus.
"""
import argparse
import re
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

POLA = re.compile(r"adegan(\d+)_f(\d+)\.jpg$")


def kelompok_file(folder):
    d = {}
    for p in sorted(folder.glob("adegan*_f*.jpg")):
        m = POLA.match(p.name)
        if m:
            d.setdefault(int(m.group(1)), []).append(p)
    return d


def kecil(path):
    im = Image.open(path).convert("L").resize((16, 12), Image.BOX)
    return np.asarray(im).astype(float)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("sesi")
    ap.add_argument("--ambang", type=float, default=0.22,
                    help="jarak maksimum dua adegan berurutan dianggap satu grup")
    a = ap.parse_args()

    folder = Path.home() / "JARVIS-BOX" / "foto_cam" / a.sesi
    adegan = kelompok_file(folder)
    if not adegan:
        raise SystemExit(f"Tidak ada foto adeganNN_fK.jpg di {folder}")

    urut = sorted(adegan)
    thumb = {n: kecil(adegan[n][0]) for n in urut}

    grup = [[urut[0]]]
    print(f"{len(urut)} adegan di {folder}\n")
    print("Jarak antar adegan berurutan (0 = identik, makin besar makin beda):")
    for n0, n1 in zip(urut, urut[1:]):
        jarak = float(np.abs(thumb[n0] - thumb[n1]).mean() / 255)
        sama = jarak <= a.ambang
        print(f"  adegan{n0:02d} -> adegan{n1:02d}: {jarak:.3f}  "
              f"{'sama grup' if sama else 'GRUP BARU'}")
        if sama:
            grup[-1].append(n1)
        else:
            grup.append([n1])

    besar = max(len(g) for g in grup)
    print(f"\n{len(urut)} adegan -> {len(grup)} grup (grup terbesar {besar} adegan)")
    print("Satu grup = kamera praktis tidak dipindah. Saat membagi train/valid,")
    print("satu grup harus utuh di satu sisi.")

    teks = [f"grup{i:02d}: " + " ".join(f"adegan{n:02d}" for n in g)
            for i, g in enumerate(grup, 1)]
    (folder / "kelompok.txt").write_text("\n".join(teks) + "\n", encoding="utf-8")
    print(f"Daftar grup: {folder / 'kelompok.txt'}")

    w, h, kolom = 213, 160, 6
    tampil = grup[:48]
    baris = (len(tampil) + kolom - 1) // kolom
    kanvas = Image.new("RGB", (kolom * w, baris * h), "white")
    for i, g in enumerate(tampil):
        im = Image.open(adegan[g[0]][0]).convert("RGB").resize((w, h))
        d = ImageDraw.Draw(im)
        d.rectangle([0, 0, 120, 14], fill="black")
        d.text((3, 1), f"grup{i + 1:02d} ({len(g)} adegan)", fill="white")
        kanvas.paste(im, ((i % kolom) * w, (i // kolom) * h))
    out = Path.home() / "JARVIS-BOX" / f"kelompok_{a.sesi}.jpg"
    kanvas.save(out, quality=88)
    print(f"Gambar ringkasan: {out}")


if __name__ == "__main__":
    main()
