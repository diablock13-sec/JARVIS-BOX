#!/usr/bin/env python3
"""Tampilkan foto api satu per satu di layar, lalu foto pakai ESP32-CAM.
Tekan q untuk berhenti.
"""
import argparse, glob, os, time, urllib.request
import cv2

p = argparse.ArgumentParser()
p.add_argument("--ip", default="10.214.193.20")
p.add_argument("--folder", required=True)
p.add_argument("--sesi", default="api_layar_s1")
p.add_argument("--tunggu", type=float, default=2.5, help="detik jeda sebelum foto")
p.add_argument("--root", default=os.path.expanduser("~/JARVIS-BOX/foto_cam"))
a = p.parse_args()

out = os.path.join(a.root, a.sesi)
os.makedirs(out, exist_ok=True)
url = f"http://{a.ip}/capture"

files = sorted(glob.glob(os.path.join(os.path.expanduser(a.folder), "*.jpg")))
print(f"{len(files)} gambar ditemukan")

cv2.namedWindow("api", cv2.WND_PROP_FULLSCREEN)
cv2.setWindowProperty("api", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

for i, f in enumerate(files, 1):
    img = cv2.imread(f)
    if img is None:
        continue
    cv2.imshow("api", img)
    if cv2.waitKey(int(a.tunggu * 1000)) & 0xFF == ord("q"):
        break
    try:
        data = urllib.request.urlopen(url, timeout=10).read()
        nama = f"{a.sesi}_{i:03d}_{os.path.basename(f)}"
        open(os.path.join(out, nama), "wb").write(data)
        print(f"[{i}/{len(files)}] {nama}")
    except Exception as e:
        print(f"[{i}] GAGAL: {e}")

cv2.destroyAllWindows()
