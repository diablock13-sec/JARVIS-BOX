#!/usr/bin/env python3
"""Ukur best_v3.pt pada foto kamera.
Pakai:
  python3 cam/evaluasi_cam.py --api foto_cam/api_layar_s2
  python3 cam/evaluasi_cam.py --api foto_cam/api_layar_s2 --bukan foto_cam/bukan_api_s1
"""
import argparse, glob, os
from ultralytics import YOLO

p = argparse.ArgumentParser()
p.add_argument("--model", default=os.path.expanduser("~/JARVIS-BOX/final_v3/best_v3.pt"))
p.add_argument("--api", required=True)
p.add_argument("--bukan", default=None)
p.add_argument("--imgsz", type=int, default=640)
a = p.parse_args()

model = YOLO(a.model)
ambang = [0.15, 0.20, 0.30]

def skor(folder):
    hasil = []
    for f in sorted(glob.glob(os.path.join(os.path.expanduser(folder), "*.jpg"))):
        r = model.predict(f, imgsz=a.imgsz, conf=0.05, verbose=False)[0]
        c = r.boxes.conf.tolist() if len(r.boxes) else []
        hasil.append((os.path.basename(f), max(c) if c else 0.0))
    return hasil

api = skor(a.api)
print("\n== API ==")
for n, s in sorted(api, key=lambda x: x[1]):
    print(f"{s:.2f}  {n}")
for t in ambang:
    tp = sum(s >= t for _, s in api)
    print(f"ambang {t:.2f}: recall {tp}/{len(api)} = {tp/len(api):.2f}")

if a.bukan:
    bk = skor(a.bukan)
    print("\n== BUKAN API ==")
    for n, s in sorted(bk, key=lambda x: -x[1]):
        print(f"{s:.2f}  {n}")
    for t in ambang:
        fp = sum(s >= t for _, s in bk)
        print(f"ambang {t:.2f}: salah deteksi {fp}/{len(bk)}")
