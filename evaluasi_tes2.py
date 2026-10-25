import glob, hashlib, os
from ultralytics import YOLO

def md5(f): return hashlib.md5(open(f, "rb").read()).hexdigest()

api = sorted(glob.glob("foto_tes2/api/*"))
bukan = sorted(glob.glob("foto_tes2/bukan_api/*"))

lain = set(md5(f) for f in glob.glob("foto_tes/*") + glob.glob("negatif/Internet/*"))
dup = [f for f in api + bukan if md5(f) in lain]
print("duplikat dengan foto_tes / negatif latihan:", len(dup))

def skor(model, files):
    out = []
    for r in model.predict(source=files, imgsz=640, conf=0.05, verbose=False, stream=True):
        out.append((os.path.basename(r.path), max([float(b.conf) for b in r.boxes], default=0.0)))
    return out

for nama in ["best.pt", "best_v2.pt"]:
    m = YOLO(nama)
    sa, sb = skor(m, api), skor(m, bukan)
    print(f"\n===== {nama}")
    print("thr   TP  FN  FP  TN  recall  specificity")
    for thr in [0.10, 0.15, 0.20, 0.30, 0.40, 0.50]:
        tp = sum(s >= thr for _, s in sa); fn = len(sa) - tp
        fp = sum(s >= thr for _, s in sb); tn = len(sb) - fp
        print(f"{thr:.2f}  {tp:2}  {fn:2}  {fp:2}  {tn:2}   {tp/len(sa):.2f}    {tn/len(sb):.2f}")
    if nama == "best_v2.pt":
        print("\nApi yang terlewat pada thr 0.15:")
        for n, s in sa:
            if s < 0.15: print(f"  {s:.2f}  {n[:50]}")
        print("Bukan api yang salah terdeteksi pada thr 0.15:")
        for n, s in sb:
            if s >= 0.15: print(f"  {s:.2f}  {n[:50]}")
