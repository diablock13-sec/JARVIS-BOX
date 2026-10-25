#!/usr/bin/env python3
import argparse, shutil, sys
from pathlib import Path

EKS = {".jpg", ".jpeg", ".png"}
NEG_TRAIN = ["camA_terang", "camA_redup", "camA_jendela", "camA_pemicu"]
NEG_VALID = ["camA_val"]
POS_TRAIN = ["camA_layar_train"]
POS_VALID = ["camA_layar_val"]
DILARANG = {"foto_tes3", "api_layar_s2", "bukan_api_s1", "camB_uji", "lama_kamera1"}

def gambar(folder):
    if not folder.is_dir():
        return []
    return sorted(p for p in folder.rglob("*") if p.suffix.lower() in EKS)

def cari_label(img):
    for c in (img.with_suffix(".txt"),
              img.parent / "labels" / (img.stem + ".txt"),
              img.parent.parent / "labels" / (img.stem + ".txt")):
        if c.is_file():
            return c
    return None

def main():
    a = argparse.ArgumentParser()
    a.add_argument("--v3", default="dataset_v3")
    a.add_argument("--v4", default="dataset_v4")
    a.add_argument("--cam", default="foto_cam")
    a.add_argument("--salin-neg", type=int, default=2)
    a.add_argument("--salin-pos", type=int, default=3)
    a.add_argument("--tulis", action="store_true")
    a = a.parse_args()

    v3, v4, cam = Path(a.v3), Path(a.v4), Path(a.cam)
    for s in ("train", "valid", "test"):
        if not (v3 / s / "images").is_dir():
            sys.exit(f"Tidak ada {v3/s/'images'} - cek --v3")
    if v4.exists() and a.tulis:
        sys.exit(f"{v4} sudah ada. Hapus atau ganti nama dulu.")

    rencana, laporan = [], []
    def tambah(split, jenis, sesi, kali):
        fs = gambar(cam / sesi)
        ok = 0
        for f in fs:
            if jenis == "neg":
                rencana.append((split, f, None, kali)); ok += 1
            else:
                lb = cari_label(f)
                if lb is None:
                    print(f"  lewati (tanpa label): {f}")
                    continue
                rencana.append((split, f, lb, kali)); ok += 1
        laporan.append((split, jenis, sesi, len(fs), ok, kali))

    for s in NEG_TRAIN: tambah("train", "neg", s, a.salin_neg)
    for s in NEG_VALID: tambah("valid", "neg", s, 1)
    for s in POS_TRAIN: tambah("train", "pos", s, a.salin_pos)
    for s in POS_VALID: tambah("valid", "pos", s, 1)

    assert not any(p in DILARANG for r in rencana for p in r[1].parts)

    n3 = {s: len(gambar(v3 / s / "images")) for s in ("train", "valid", "test")}
    tambahan = {"train": 0, "valid": 0}
    neg = {"train": 0, "valid": 0}
    for split, f, lb, k in rencana:
        tambahan[split] += k
        if lb is None: neg[split] += k

    print("\nSesi              split  jenis  foto  dipakai  salin")
    for sp, j, se, tot, ok, k in laporan:
        print(f"{se:<17} {sp:<6} {j:<5} {tot:>5} {ok:>8} {k:>5}")
    print("\nPerkiraan hasil:")
    for s in ("train", "valid"):
        print(f"  {s}: v3 {n3[s]} + baru {tambahan[s]} = {n3[s]+tambahan[s]}  (negatif baru {neg[s]})")
    print(f"  test: {n3['test']} (disalin apa adanya)")
    print("Catatan: negatif v3 (4 + 124 foto internet) belum dihitung di atas.")

    if not a.tulis:
        print("\nPratinjau saja. Tambahkan --tulis untuk membuat dataset_v4.")
        return

    for s in ("train", "valid", "test"):
        for sub in ("images", "labels"):
            (v4 / s / sub).mkdir(parents=True)
            src = v3 / s / sub
            if src.is_dir():
                for f in src.iterdir():
                    shutil.copy2(f, v4 / s / sub / f.name)
    for split, f, lb, k in rencana:
        for i in range(k):
            nama = f"{f.parent.name}_{f.stem}" + (f"_c{i+1}" if k > 1 else "")
            shutil.copy2(f, v4 / split / "images" / (nama + f.suffix.lower()))
            lbl = v4 / split / "labels" / (nama + ".txt")
            if lb is None: lbl.write_text("")
            else: shutil.copy2(lb, lbl)

    (v4 / "data.yaml").write_text(
        f"path: {v4.resolve()}\ntrain: train/images\nval: valid/images\ntest: test/images\n"
        "nc: 2\nnames: ['Fire', 'Smoke']\n")
    for s in ("train", "valid", "test"):
        ni = len(list((v4/s/'images').iterdir()))
        nl = sum(1 for l in (v4/s/'labels').glob('*.txt') if l.stat().st_size == 0)
        print(f"{s}: {ni} gambar, {nl} negatif ({100*nl/max(ni,1):.1f}%)")
    print(f"Selesai: {v4}")

main()
