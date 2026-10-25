#!/usr/bin/env python3
"""Penggambar kotak YOLO untuk foto kamera.
Pakai (dari ~/JARVIS-BOX, venv aktif):
  python3 cam/label_kotak.py
  python3 cam/label_kotak.py camA_layar_train --semua
Mouse: seret tombol kiri = gambar kotak dengan kelas yang aktif.
Tombol: 0 = Fire, 1 = Smoke, u = batalkan kotak terakhir, c = hapus semua kotak,
  y = salin kotak dari frame pasangan (f1 <-> f2), Enter/Spasi = simpan lalu lanjut,
  n = simpan tanpa kotak (negatif), k = lewati tanpa mengubah,
  d = buang foto (dipindah ke foto_cam/dibuang), b = mundur, q = selesai.
"""
import argparse
import glob
import os
import shutil

import cv2

ROOT = os.path.expanduser("~/JARVIS-BOX/foto_cam")
NAMA = {0: "Fire", 1: "Smoke"}
WARNA = {0: (0, 0, 255), 1: (255, 170, 0)}
FONT = cv2.FONT_HERSHEY_SIMPLEX

ap = argparse.ArgumentParser()
ap.add_argument("folder", nargs="*", default=["camA_layar_train", "camA_layar_val"])
ap.add_argument("--semua", action="store_true")
ap.add_argument("--skala", type=float, default=1.4)
a = ap.parse_args()


def label_path(jpg):
    return os.path.splitext(jpg)[0] + ".txt"


def baca_label(txt):
    kotak = []
    if os.path.exists(txt):
        with open(txt) as f:
            for baris in f.read().splitlines():
                p = baris.split()
                if len(p) == 5:
                    kotak.append([int(p[0])] + [float(x) for x in p[1:]])
    return kotak


def tulis_label(txt, kotak):
    with open(txt, "w") as f:
        for c, cx, cy, w, h in kotak:
            f.write(f"{int(c)} {cx:.6f} {cy:.6f} {w:.6f} {h:.6f}\n")


def pasangan(jpg):
    if "_f1." in jpg:
        return jpg.replace("_f1.", "_f2.")
    if "_f2." in jpg:
        return jpg.replace("_f2.", "_f1.")
    return None


def buang(jpg):
    tujuan = os.path.join(ROOT, "dibuang")
    os.makedirs(tujuan, exist_ok=True)
    fo = os.path.basename(os.path.dirname(jpg))
    for src in (jpg, label_path(jpg)):
        if os.path.exists(src):
            shutil.move(src, os.path.join(tujuan, f"{fo}__{os.path.basename(src)}"))


def daftar(semua):
    hasil = []
    for fo in a.folder:
        for f in sorted(glob.glob(os.path.join(ROOT, fo, "*.jpg"))):
            if semua or not baca_label(label_path(f)):
                hasil.append(f)
    return hasil


files = daftar(a.semua)
print(f"{len(files)} foto untuk diproses")
if not files:
    raise SystemExit

st = {"kotak": [], "kelas": 0, "awal": None, "kini": None, "W": 1, "H": 1}


def mouse(ev, x, y, flags, param):
    W, H = st["W"], st["H"]
    x = min(max(x, 0), W)
    y = min(max(y, 0), H)
    if ev == cv2.EVENT_LBUTTONDOWN:
        st["awal"] = (x, y)
        st["kini"] = (x, y)
    elif ev == cv2.EVENT_MOUSEMOVE and st["awal"] is not None:
        st["kini"] = (x, y)
    elif ev == cv2.EVENT_LBUTTONUP and st["awal"] is not None:
        x0, y0 = st["awal"]
        st["awal"] = None
        st["kini"] = None
        xa, xb = sorted((x0, x))
        ya, yb = sorted((y0, y))
        if xb - xa > 5 and yb - ya > 5:
            st["kotak"].append([st["kelas"], (xa + xb) / 2 / W, (ya + yb) / 2 / H,
                                (xb - xa) / W, (yb - ya) / H])


def gambar(img, judul):
    tampil = img.copy()
    H, W = tampil.shape[:2]
    for c, cx, cy, w, h in st["kotak"]:
        warna = WARNA.get(int(c), (0, 255, 0))
        p0 = (int((cx - w / 2) * W), int((cy - h / 2) * H))
        p1 = (int((cx + w / 2) * W), int((cy + h / 2) * H))
        cv2.rectangle(tampil, p0, p1, warna, 2)
        cv2.putText(tampil, NAMA.get(int(c), str(int(c))), (p0[0] + 3, p0[1] + 16),
                    FONT, 0.55, warna, 2)
    if st["awal"] is not None and st["kini"] is not None:
        cv2.rectangle(tampil, st["awal"], st["kini"], WARNA[st["kelas"]], 1)
    cv2.rectangle(tampil, (0, 0), (W, 24), (0, 0, 0), -1)
    cv2.putText(tampil, f"{judul} | kelas: {NAMA[st['kelas']]} | kotak: {len(st['kotak'])}",
                (6, 17), FONT, 0.5, (255, 255, 255), 1)
    cv2.rectangle(tampil, (0, H - 22), (W, H), (0, 0, 0), -1)
    cv2.putText(tampil, "0 Fire 1 Smoke | u undo c hapus y pasangan | Enter simpan n negatif k lewati d buang b mundur q selesai",
                (6, H - 7), FONT, 0.4, (255, 255, 255), 1)
    return tampil


cv2.namedWindow("label")
cv2.setMouseCallback("label", mouse)

i = 0
selesai = False
while 0 <= i < len(files) and not selesai:
    jpg = files[i]
    im = cv2.imread(jpg)
    if im is None:
        i += 1
        continue
    img = cv2.resize(im, None, fx=a.skala, fy=a.skala)
    st["H"], st["W"] = img.shape[:2]
    st["kotak"] = baca_label(label_path(jpg))
    st["awal"] = None
    st["kini"] = None
    judul = f"[{i + 1}/{len(files)}] {os.path.basename(os.path.dirname(jpg))}/{os.path.basename(jpg)}"
    while True:
        cv2.imshow("label", gambar(img, judul))
        k = cv2.waitKey(30) & 0xFF
        if k in (10, 13, 32):
            if not st["kotak"]:
                print("  belum ada kotak: gambar kotak, atau tekan n (negatif), k (lewati), d (buang)")
                continue
            tulis_label(label_path(jpg), st["kotak"])
            i += 1
            break
        elif k == ord("n"):
            tulis_label(label_path(jpg), [])
            i += 1
            break
        elif k == ord("k"):
            i += 1
            break
        elif k == ord("b"):
            i = max(0, i - 1)
            break
        elif k == ord("d"):
            buang(jpg)
            files.pop(i)
            print("  dibuang:", os.path.basename(jpg))
            break
        elif k == ord("q"):
            selesai = True
            break
        elif k in (ord("0"), ord("1")):
            st["kelas"] = k - ord("0")
        elif k == ord("u"):
            st["kotak"] = st["kotak"][:-1]
        elif k == ord("c"):
            st["kotak"] = []
        elif k == ord("y"):
            p = pasangan(jpg)
            kp = baca_label(label_path(p)) if p else []
            if kp:
                st["kotak"] = kp
            else:
                print("  pasangan tidak punya kotak")

cv2.destroyAllWindows()

sisa = []
for fo in a.folder:
    for f in sorted(glob.glob(os.path.join(ROOT, fo, "*.jpg"))):
        if not baca_label(label_path(f)):
            sisa.append(os.path.relpath(f, ROOT))
print(f"Selesai. Foto yang masih tanpa kotak: {len(sisa)}")
for s in sisa:
    print("  ", s)
