#!/usr/bin/env python3
"""Inferensi NCNN murni (tanpa PyTorch) untuk model YOLO11n hasil ekspor 480x640.

Pakai:
    python3 infer_ncnn.py FOTO_ATAU_FOLDER [opsi]

Opsi:
    --model  FOLDER   folder model NCNN (default: best_v3_ncnn_model)
    --ambang 0.20     foto dihitung terdeteksi bila skor tertinggi >= ambang
    --simpan FOLDER   simpan gambar berkotak ke folder ini (untuk dilihat)
    --ulang  N        ukur kecepatan: ulangi N kali pada foto pertama
    --thread N        jumlah thread CPU (default 4)

Keluaran per foto: skor tertinggi Fire, skor tertinggi Smoke, jumlah kotak
(setelah NMS), dan waktu (ms). Bila di samping foto ada file .txt label,
foto dikelompokkan: api (ada kotak), negatif (txt kosong), tanpa label.
Skor visual untuk skor gabungan = skor tertinggi dari kedua kelas.

Frame kamera A (640x480) diberikan apa adanya tanpa bantalan. Gambar dengan
rasio lain di-letterbox ke 640x480 (bantalan abu-abu) seperti Ultralytics.
"""
import argparse
import time
from pathlib import Path

import cv2
import numpy as np

NAMA = {0: "Fire", 1: "Smoke"}
WARNA = {0: (0, 0, 255), 1: (255, 170, 0)}
EXT = {".jpg", ".jpeg", ".png", ".bmp"}
IN_W, IN_H = 640, 480          # sesuai ekspor imgsz=[480,640]


def muat_model(folder, thread):
    import ncnn
    folder = Path(folder)
    param = folder / "model.ncnn.param"
    bin_ = folder / "model.ncnn.bin"
    if not param.exists() or not bin_.exists():
        raise SystemExit(f"model.ncnn.param atau model.ncnn.bin tidak ada di {folder}")
    net = ncnn.Net()
    net.opt.use_vulkan_compute = False
    net.opt.num_threads = thread
    net.load_param(str(param))
    net.load_model(str(bin_))
    return ncnn, net


def letterbox(img):
    h, w = img.shape[:2]
    if (w, h) == (IN_W, IN_H):
        return img, 1.0, 0, 0
    r = min(IN_H / h, IN_W / w)
    nw, nh = round(w * r), round(h * r)
    kecil = cv2.resize(img, (nw, nh), interpolation=cv2.INTER_LINEAR)
    dw, dh = (IN_W - nw) / 2, (IN_H - nh) / 2
    atas, bawah = round(dh - 0.1), round(dh + 0.1)
    kiri, kanan = round(dw - 0.1), round(dw + 0.1)
    out = cv2.copyMakeBorder(kecil, atas, bawah, kiri, kanan,
                             cv2.BORDER_CONSTANT, value=(114, 114, 114))
    return out, r, kiri, atas


def prediksi(ncnn, net, img, ambang):
    """Kembalikan (skor_max per kelas [Fire, Smoke], daftar kotak, ms)."""
    t0 = time.perf_counter()
    lb, r, pad_x, pad_y = letterbox(img)
    rgb = cv2.cvtColor(lb, cv2.COLOR_BGR2RGB)
    chw = np.ascontiguousarray(rgb.transpose(2, 0, 1), dtype=np.float32) / 255.0
    mat_in = ncnn.Mat(chw)
    with net.create_extractor() as ex:
        ex.input(net.input_names()[0], mat_in)
        out = np.array(ex.extract(net.output_names()[0])[1])
    # out: (6, N) = cx, cy, w, h, skor Fire, skor Smoke
    pred = out.T
    skor = pred[:, 4:]
    skor_max = skor.max(axis=0)
    kelas = skor.argmax(axis=1)
    conf = skor.max(axis=1)
    ada = conf >= ambang
    kotak = []
    for c in range(skor.shape[1]):
        idx = np.where(ada & (kelas == c))[0]
        if idx.size == 0:
            continue
        cx, cy, w, h = (pred[idx, i] for i in range(4))
        xywh = np.stack([cx - w / 2, cy - h / 2, w, h], axis=1)
        keep = cv2.dnn.NMSBoxes(xywh.tolist(), conf[idx].tolist(), float(ambang), 0.7)
        for k in np.array(keep).flatten():
            x, y, bw, bh = xywh[k]
            x1 = (x - pad_x) / r
            y1 = (y - pad_y) / r
            kotak.append((c, float(conf[idx][k]), x1, y1, x1 + bw / r, y1 + bh / r))
    ms = (time.perf_counter() - t0) * 1000
    return skor_max, kotak, ms


def gambar_kotak(img, kotak):
    out = img.copy()
    for c, s, x1, y1, x2, y2 in kotak:
        p1, p2 = (int(x1), int(y1)), (int(x2), int(y2))
        cv2.rectangle(out, p1, p2, WARNA[c], 2)
        cv2.putText(out, f"{NAMA[c]} {s:.2f}", (p1[0] + 3, max(p1[1] + 16, 16)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, WARNA[c], 2)
    return out


def kelompok(jpg):
    txt = jpg.with_suffix(".txt")
    if not txt.exists():
        return "tanpa label"
    ada = any(len(b.split()) >= 5 for b in txt.read_text().splitlines())
    return "api" if ada else "negatif"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("sumber")
    ap.add_argument("--model", default="best_v3_ncnn_model")
    ap.add_argument("--ambang", type=float, default=0.20)
    ap.add_argument("--simpan")
    ap.add_argument("--ulang", type=int, default=0)
    ap.add_argument("--thread", type=int, default=4)
    a = ap.parse_args()

    ncnn, net = muat_model(a.model, a.thread)
    src = Path(a.sumber)
    files = [src] if src.is_file() else sorted(p for p in src.iterdir()
                                              if p.suffix.lower() in EXT)
    if not files:
        raise SystemExit("tidak ada foto")
    simpan = Path(a.simpan) if a.simpan else None
    if simpan:
        simpan.mkdir(parents=True, exist_ok=True)

    if a.ulang:
        img = cv2.imread(str(files[0]))
        for _ in range(3):
            prediksi(ncnn, net, img, a.ambang)   # pemanasan
        waktu = [prediksi(ncnn, net, img, a.ambang)[2] for _ in range(a.ulang)]
        print(f"Kecepatan pada {files[0].name} ({a.ulang}x, thread {a.thread}): "
              f"rata-rata {np.mean(waktu):.0f} ms, min {min(waktu):.0f}, "
              f"maks {max(waktu):.0f}")
        return

    hitung = {}
    semua_ms = []
    print(f"{'foto':44} {'Fire':>5} {'Smoke':>6} {'kotak':>5} {'ms':>6}  kelompok")
    for f in files:
        img = cv2.imread(str(f))
        if img is None:
            print(f"{f.name[:44]:44} tidak bisa dibaca")
            continue
        skor, kotak, ms = prediksi(ncnn, net, img, a.ambang)
        semua_ms.append(ms)
        g = kelompok(f)
        terdeteksi = bool(skor.max() >= a.ambang)
        n, d = hitung.get(g, (0, 0))
        hitung[g] = (n + 1, d + int(terdeteksi))
        print(f"{f.name[:44]:44} {skor[0]:5.2f} {skor[1]:6.2f} {len(kotak):5d} "
              f"{ms:6.0f}  {g}{' *' if terdeteksi else ''}")
        if simpan:
            cv2.imwrite(str(simpan / f.name), gambar_kotak(img, kotak))

    print(f"\nAmbang {a.ambang:.2f}  (* = terdeteksi). Ringkasan per kelompok:")
    for g, (n, d) in sorted(hitung.items()):
        print(f"  {g}: {d} dari {n} terdeteksi")
    if semua_ms:
        print(f"Waktu rata-rata {np.mean(semua_ms):.0f} ms per foto "
              f"(termasuk letterbox, NMS; foto pertama bisa lebih lambat)")


if __name__ == "__main__":
    main()
