#!/usr/bin/env python3
"""Ringkasan status label foto kamera dan dataset_v4.

Pakai (dari ~/JARVIS-BOX, venv aktif):
    python3 cam/status_label.py

Menampilkan:
1. isi folder cam/ dan folder utama di ~/JARVIS-BOX
2. status label tiap folder foto di foto_cam/ (dan pra_label_cek/ bila ada)
3. isi dataset_v4: jumlah gambar dan label per split, jumlah kotak per kelas,
   gambar tanpa label, label tanpa gambar, dan isi data.yaml
Hanya membaca; tidak mengubah atau memindah file apa pun.
"""
from collections import Counter
from pathlib import Path

ROOT = Path.home() / "JARVIS-BOX"
EXT = {".jpg", ".jpeg", ".png"}
NAMA = {0: "Fire", 1: "Smoke"}


def kelas_di(txt):
    """Daftar kelas tiap kotak; [] = file kosong (negatif); None = file tidak ada."""
    if not txt.exists():
        return None
    out = []
    for baris in txt.read_text().splitlines():
        p = baris.split()
        if len(p) >= 5:
            out.append(int(float(p[0])))
    return out


def nama_kelas(c):
    return NAMA.get(c, str(c))


def ringkas_foto(folder):
    imgs = sorted(p for p in folder.iterdir() if p.suffix.lower() in EXT)
    if not imgs:
        return
    tanpa, negatif, berkotak = [], 0, 0
    kotak = Counter()
    for p in imgs:
        k = kelas_di(p.with_suffix(".txt"))
        if k is None:
            tanpa.append(p.name)
        elif not k:
            negatif += 1
        else:
            berkotak += 1
            kotak.update(k)
    per_kelas = ", ".join(f"{nama_kelas(c)} {n}" for c, n in sorted(kotak.items())) or "-"
    print(f"  {folder.name}: {len(imgs)} foto | berkotak {berkotak} | "
          f"negatif (txt kosong) {negatif} | BELUM ada txt {len(tanpa)} | kotak: {per_kelas}")
    if tanpa:
        contoh = ", ".join(tanpa[:6]) + (" ..." if len(tanpa) > 6 else "")
        print(f"      belum diproses, mis.: {contoh}")


def ringkas_dataset(root):
    for split in ["train", "valid", "val", "test"]:
        img_dir, lbl_dir = root / split / "images", root / split / "labels"
        if not img_dir.exists():
            continue
        imgs = [p for p in img_dir.iterdir() if p.suffix.lower() in EXT]
        stems = {p.stem for p in imgs}
        kosong = tanpa = 0
        kotak = Counter()
        for p in imgs:
            k = kelas_di(lbl_dir / (p.stem + ".txt"))
            if k is None:
                tanpa += 1
            elif not k:
                kosong += 1
            else:
                kotak.update(k)
        yatim = [t for t in lbl_dir.glob("*.txt") if t.stem not in stems] if lbl_dir.exists() else []
        per_kelas = ", ".join(f"{nama_kelas(c)} {n}" for c, n in sorted(kotak.items())) or "-"
        print(f"  {split}: {len(imgs)} gambar | label kosong (negatif) {kosong} | "
              f"tanpa file label {tanpa} | label tanpa gambar {len(yatim)} | kotak: {per_kelas}")
    yaml = root / "data.yaml"
    if yaml.exists():
        print("\n  isi data.yaml:")
        for baris in yaml.read_text().splitlines()[:25]:
            print("    " + baris)
    else:
        print("\n  data.yaml tidak ada")


def main():
    print("== isi ~/JARVIS-BOX/cam ==")
    cam = ROOT / "cam"
    if cam.exists():
        print("  " + ", ".join(sorted(p.name for p in cam.iterdir())))
    else:
        print("  folder cam tidak ada")

    print("\n== folder utama di ~/JARVIS-BOX ==")
    print("  " + ", ".join(sorted(p.name for p in ROOT.iterdir() if p.is_dir() and p.name != "venv")))

    print("\n== status label foto ==")
    for induk in [ROOT / "foto_cam", ROOT / "pra_label_cek"]:
        if not induk.exists():
            print(f"  {induk.name}: tidak ada")
            continue
        print(f" [{induk.name}]")
        ada = False
        if any(p.suffix.lower() in EXT for p in induk.iterdir() if p.is_file()):
            ringkas_foto(induk)
            ada = True
        for sub in sorted(p for p in induk.iterdir() if p.is_dir()):
            if any(q.suffix.lower() in EXT for q in sub.iterdir() if q.is_file()):
                ringkas_foto(sub)
                ada = True
        if not ada:
            print("  (tidak ada foto)")

    print("\n== dataset_v4 ==")
    v4 = ROOT / "dataset_v4"
    if v4.exists():
        ringkas_dataset(v4)
    else:
        print("  dataset_v4 tidak ada")


if __name__ == "__main__":
    main()
