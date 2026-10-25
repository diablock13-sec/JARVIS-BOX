#!/usr/bin/env python3
"""Tambahkan foto layar berkotak (kamera A) ke dataset_v4.

Pakai (dari ~/JARVIS-BOX, venv aktif):
    python3 cam/tambah_layar_v4.py                 # hanya menampilkan rencana
    python3 cam/tambah_layar_v4.py --jalan         # benar-benar menyalin
    python3 cam/tambah_layar_v4.py --jalan --salin 2

Pemetaan:
    foto_cam/camA_layar_train  ->  dataset_v4/train
    foto_cam/camA_layar_val    ->  dataset_v4/valid

Aturan:
- Foto berkotak di train disalin --salin kali (default 3). Foto negatif
  (file txt kosong) disalin 1 kali. Di valid semuanya 1 kali.
- Foto tanpa file txt dilewati (belum diproses dengan label_kotak.py).
- Label diperiksa: 5 kolom, kelas 0 atau 1, nilai 0 sampai 1.
  Foto bermasalah dilewati dan dilaporkan.
- Nama file baru diawali cam_; file yang sudah ada dilewati, jadi aman
  dijalankan ulang. Jalankan lagi bila dataset_v4 dibuat ulang.
Tanpa --jalan tidak ada file yang diubah.
"""
import argparse
import shutil
from collections import Counter
from pathlib import Path

ROOT = Path.home() / "JARVIS-BOX"
FOTO = ROOT / "foto_cam"
V4 = ROOT / "dataset_v4"
EXT = {".jpg", ".jpeg", ".png"}
PETA = [("camA_layar_train", "train"), ("camA_layar_val", "valid")]
NAMA = {0: "Fire", 1: "Smoke"}


def baca(txt):
    """Kembalikan (daftar kelas tiap kotak, masalah). Masalah None bila beres."""
    kelas = []
    for no, baris in enumerate(txt.read_text().splitlines(), 1):
        if not baris.strip():
            continue
        p = baris.split()
        if len(p) != 5:
            return None, f"baris {no}: kolom bukan 5"
        try:
            c = int(float(p[0]))
            nilai = [float(x) for x in p[1:]]
        except ValueError:
            return None, f"baris {no}: bukan angka"
        if c not in NAMA:
            return None, f"baris {no}: kelas {c} tidak dikenal"
        if any(v < 0 or v > 1 for v in nilai) or nilai[2] <= 0 or nilai[3] <= 0:
            return None, f"baris {no}: nilai di luar 0..1 atau ukuran nol"
        kelas.append(c)
    return kelas, None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jalan", action="store_true", help="benar-benar menyalin")
    ap.add_argument("--salin", type=int, default=3,
                    help="berapa kali foto berkotak di train disalin (default 3)")
    a = ap.parse_args()

    if not V4.exists():
        raise SystemExit(f"{V4} tidak ada")

    total = {}
    for folder, split in PETA:
        sumber = FOTO / folder
        if not sumber.exists():
            print(f"[{folder}] folder tidak ada, dilewati")
            continue
        img_dir, lbl_dir = V4 / split / "images", V4 / split / "labels"
        img_dir.mkdir(parents=True, exist_ok=True)
        lbl_dir.mkdir(parents=True, exist_ok=True)

        belum, sudah = [], 0
        masalah = []
        gambar = negatif = 0
        kotak = Counter()
        for jpg in sorted(p for p in sumber.iterdir() if p.suffix.lower() in EXT):
            txt = jpg.with_suffix(".txt")
            if not txt.exists():
                belum.append(jpg.name)
                continue
            kelas, salah = baca(txt)
            if salah:
                masalah.append(f"{jpg.name}: {salah}")
                continue
            n = a.salin if (split == "train" and kelas) else 1
            for k in range(n):
                nama = f"cam_{folder}_{jpg.stem}" + (f"_c{k + 1}" if n > 1 else "")
                dst_img = img_dir / (nama + jpg.suffix.lower())
                dst_lbl = lbl_dir / (nama + ".txt")
                if dst_img.exists() and dst_lbl.exists():
                    sudah += 1
                    continue
                if a.jalan:
                    shutil.copy2(jpg, dst_img)
                    shutil.copy2(txt, dst_lbl)
                gambar += 1
                if kelas:
                    kotak.update(kelas)
                else:
                    negatif += 1

        per_kelas = ", ".join(f"{NAMA[c]} {n}" for c, n in sorted(kotak.items())) or "-"
        print(f"[{folder} -> {split}] ditambah {gambar} gambar "
              f"(negatif {negatif}) | kotak: {per_kelas} | sudah ada {sudah} "
              f"| belum diproses {len(belum)} | bermasalah {len(masalah)}")
        for m in masalah[:10]:
            print("    MASALAH:", m)
        if belum:
            print("    belum ada txt, mis.:", ", ".join(belum[:5]))
        total[split] = gambar

    if a.jalan:
        print("\nSelesai menyalin. Cek hasilnya dengan: python3 cam/status_label.py")
    else:
        print("\nIni hanya rencana. Tambahkan --jalan untuk benar-benar menyalin.")


if __name__ == "__main__":
    main()
