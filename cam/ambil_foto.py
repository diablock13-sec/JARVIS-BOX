#!/usr/bin/env python3
"""Ambil foto dari ESP32-CAM per sesi.
Contoh:
  python3 ambil_foto.py --sesi bukan_api_s1 --jumlah 40 --jeda 3
"""
import argparse, os, time, urllib.request
from datetime import datetime

p = argparse.ArgumentParser()
p.add_argument("--ip", default="10.214.193.20")
p.add_argument("--sesi", required=True, help="nama folder sesi")
p.add_argument("--jumlah", type=int, default=30)
p.add_argument("--jeda", type=float, default=3.0, help="detik antar foto")
p.add_argument("--root", default=os.path.expanduser("~/JARVIS-BOX/foto_cam"))
a = p.parse_args()

folder = os.path.join(a.root, a.sesi)
os.makedirs(folder, exist_ok=True)
url = f"http://{a.ip}/capture"

# buang 3 frame awal supaya auto exposure stabil
for _ in range(3):
    try:
        urllib.request.urlopen(url, timeout=10).read()
    except Exception:
        pass
    time.sleep(0.5)

ok = 0
for i in range(1, a.jumlah + 1):
    try:
        data = urllib.request.urlopen(url, timeout=10).read()
        if len(data) < 2000 or data[:2] != b"\xff\xd8":
            raise ValueError(f"data tidak valid ({len(data)} byte)")
        nama = f"{a.sesi}_{datetime.now():%H%M%S}_{i:03d}.jpg"
        with open(os.path.join(folder, nama), "wb") as f:
            f.write(data)
        ok += 1
        print(f"[{i}/{a.jumlah}] {nama} ({len(data)//1024} KB)")
    except Exception as e:
        print(f"[{i}/{a.jumlah}] GAGAL: {e}")
    time.sleep(a.jeda)

print(f"Selesai: {ok}/{a.jumlah} foto di {folder}")
