#!/usr/bin/env python3
"""Ambil foto per ADEGAN dari ESP32-CAM lewat /capture.

Pakai (dari folder ~/JARVIS-BOX):
    python cam/ambil_adegan.py camA_terang --ip 10.42.0.21

Enter = ambil satu adegan (default 4 frame). q + Enter = selesai.
Hasil: ~/JARVIS-BOX/foto_cam/<sesi>/adegan01_f1.jpg, ...
Penomoran melanjutkan dari adegan terakhir, jadi tidak menimpa file lama.
"""
import argparse
import re
import time
from pathlib import Path
from urllib.request import urlopen

UKURAN_MINIMUM = 3000  # byte; di bawah ini dianggap mencurigakan


def ambil(ip, timeout=8):
    with urlopen(f"http://{ip}/capture", timeout=timeout) as r:
        return r.read()


def valid(data):
    return data[:2] == b"\xff\xd8" and len(data) >= UKURAN_MINIMUM


def main():
    ap = argparse.ArgumentParser(description="Ambil foto per adegan dari ESP32-CAM")
    ap.add_argument("sesi", help="nama sesi, mis. camA_terang")
    ap.add_argument("--ip", default="10.42.0.21", help="IP kamera")
    ap.add_argument("--frame", type=int, default=4, help="jumlah frame per adegan")
    ap.add_argument("--jeda", type=float, default=0.6, help="jeda antar frame (detik)")
    a = ap.parse_args()

    folder = Path.home() / "JARVIS-BOX" / "foto_cam" / a.sesi
    folder.mkdir(parents=True, exist_ok=True)

    nomor = []
    for p in folder.glob("adegan*_f1.jpg"):
        m = re.match(r"adegan(\d+)_f1$", p.stem)
        if m:
            nomor.append(int(m.group(1)))
    n = max(nomor, default=0)

    print(f"Folder : {folder}")
    print(f"Kamera : http://{a.ip}/capture | {a.frame} frame per adegan")
    print(f"Adegan yang sudah ada: {n}")
    print("Enter = ambil adegan berikutnya | q + Enter = selesai\n")

    while True:
        perintah = input(f"[adegan {n + 1:02d}] siap? ").strip().lower()
        if perintah == "q":
            break

        try:
            ambil(a.ip)  # frame pemanasan, dibuang
            time.sleep(a.jeda)
            frames = []
            for _ in range(a.frame):
                data = ambil(a.ip)
                if not valid(data):
                    raise ValueError(
                        f"frame tidak valid (ukuran {len(data)} byte, awal {data[:2]!r})"
                    )
                frames.append(data)
                time.sleep(a.jeda)
        except Exception as e:
            print(f"  GAGAL: {e}. Adegan dibuang, coba lagi.\n")
            continue

        n += 1
        for k, data in enumerate(frames, 1):
            (folder / f"adegan{n:02d}_f{k}.jpg").write_bytes(data)
        ukuran = ", ".join(f"{len(d) // 1024} KB" for d in frames)
        print(f"  OK adegan{n:02d}: {len(frames)} frame ({ukuran})\n")

    jumlah = len(list(folder.glob("adegan*.jpg")))
    print(f"\nSelesai. Total {n} adegan, {jumlah} foto di {folder}")


if __name__ == "__main__":
    main()
