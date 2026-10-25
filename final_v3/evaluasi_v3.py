import glob, os
from ultralytics import YOLO

positif = ["egor", "emma", "erik", "karsten", "landon", "malachi",
           "marc", "matt-howard", "matt-palmer", "michael"]

set1 = [(f, os.path.basename(f).startswith(tuple(positif))) for f in sorted(glob.glob("foto_tes/*"))]
set2 = [(f, True) for f in sorted(glob.glob("foto_tes2/api/*"))] + \
       [(f, False) for f in sorted(glob.glob("foto_tes2/bukan_api/*"))]

kunci = ["jordan-steranka", "dewang-gupta", "egor-vikhrev-cV7cOur4sAM", "matt-howard", "chris-leboutillier"]

def skor(model, data):
    files = [f for f, _ in data]
    out = {}
    for r in model.predict(source=files, imgsz=640, conf=0.05, verbose=False, stream=True):
        out[r.path] = max([float(b.conf) for b in r.boxes], default=0.0)
    return [(f, out[f], ada) for f, ada in data]

def tabel(hasil):
    p = sum(1 for _, _, a in hasil if a); n = len(hasil) - p
    print("thr   recall  FP(dari %d)  specificity" % n)
    for thr in [0.10, 0.15, 0.20, 0.30, 0.40, 0.50]:
        tp = sum(1 for _, s, a in hasil if a and s >= thr)
        fp = sum(1 for _, s, a in hasil if not a and s >= thr)
        print(f"{thr:.2f}  {tp/p:.2f}    {fp:2}          {(n-fp)/n:.2f}")

for nama in ["best_v2.pt", "best_v3.pt"]:
    m = YOLO(nama)
    h1, h2 = skor(m, set1), skor(m, set2)
    print(f"\n########## {nama}")
    print("--- foto_tes (14 api, 13 bukan api)"); tabel(h1)
    print("--- foto_tes2 (20 api, 14 bukan api)"); tabel(h2)
    print("--- foto kunci:")
    for f, s, a in h1 + h2:
        if any(k in f for k in kunci):
            print(f"  {s:.2f}  {'api' if a else 'bukan'}  {os.path.basename(f)[:40]}")
