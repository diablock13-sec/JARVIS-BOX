import glob, os
from ultralytics import YOLO

api = sorted(glob.glob("foto_tes3/api/*"))
bukan = sorted(glob.glob("foto_tes3/bukan_api/*"))
abu = sorted(glob.glob("foto_tes3/abu_abu/*"))

def skor(model, files):
    out = {}
    for r in model.predict(source=files, imgsz=640, conf=0.05, verbose=False, stream=True):
        out[r.path] = max([float(b.conf) for b in r.boxes], default=0.0)
    return [out[f] for f in files]

hasil = {}
for nama in ["best_v2.pt", "best_v3.pt"]:
    m = YOLO(nama)
    hasil[nama] = (skor(m, api), skor(m, bukan), skor(m, abu))

for nama, (sa, sb, sc) in hasil.items():
    print(f"\n########## {nama}  (api={len(sa)}, bukan_api={len(sb)}, abu_abu={len(sc)})")
    print("thr   recall  FP  specificity  abu_abu_terdeteksi")
    for thr in [0.10, 0.15, 0.20, 0.30, 0.40, 0.50]:
        tp = sum(s >= thr for s in sa)
        fp = sum(s >= thr for s in sb)
        ab = sum(s >= thr for s in sc)
        print(f"{thr:.2f}  {tp/len(sa):.2f}    {fp:2}  {(len(sb)-fp)/len(sb):.2f}         {ab}/{len(sc)}")

print("\n===== skor per foto: api (v2 -> v3), diurutkan dari skor v3 terendah")
for f, a, b in sorted(zip(api, hasil["best_v2.pt"][0], hasil["best_v3.pt"][0]), key=lambda x: x[2]):
    if min(a, b) < 0.30:
        print(f"  {a:.2f} -> {b:.2f}  {os.path.basename(f)[:45]}")

print("\n===== skor per foto: bukan api yang salah terdeteksi (v2 -> v3, salah satu >= 0.15)")
for f, a, b in zip(bukan, hasil["best_v2.pt"][1], hasil["best_v3.pt"][1]):
    if max(a, b) >= 0.15:
        print(f"  {a:.2f} -> {b:.2f}  {os.path.basename(f)[:45]}")
