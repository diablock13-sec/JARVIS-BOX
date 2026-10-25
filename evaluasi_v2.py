import sys
from ultralytics import YOLO

imgsz = int(sys.argv[1]) if len(sys.argv) > 1 else 640

positif = ["egor", "emma", "erik", "karsten", "landon", "malachi",
           "marc", "matt-howard", "matt-palmer", "michael"]

model = YOLO("best_v2.pt")
hasil = model.predict(source="foto_tes", imgsz=imgsz, conf=0.05, verbose=False)

data = []
for r in hasil:
    nama = r.path.split("/")[-1]
    skor = max([float(b.conf) for b in r.boxes], default=0.0)
    data.append((nama, skor, nama.startswith(tuple(positif))))

print(f"imgsz = {imgsz}")
print("Skor tertinggi per foto (P = ada api/asap, N = negatif):")
for nama, skor, ada in sorted(data, key=lambda x: -x[1]):
    print(f"{'P' if ada else 'N'}  {skor:.2f}  {nama[:45]}")

print("\nthr   TP  FN  FP  TN  recall  specificity")
for thr in [0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70]:
    tp = sum(1 for _, s, a in data if a and s >= thr)
    fn = sum(1 for _, s, a in data if a and s < thr)
    fp = sum(1 for _, s, a in data if not a and s >= thr)
    tn = sum(1 for _, s, a in data if not a and s < thr)
    print(f"{thr:.2f}  {tp:2}  {fn:2}  {fp:2}  {tn:2}   "
          f"{tp/(tp+fn):.2f}    {tn/(tn+fp):.2f}")