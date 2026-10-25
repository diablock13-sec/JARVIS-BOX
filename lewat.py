import glob, os
from ultralytics import YOLO
f = sorted(glob.glob("foto_tes3/api/*"))
for m in ("best_v3.pt", "best_v4.pt"):
    mod = YOLO(m)
    for p, r in zip(f, mod.predict(f, imgsz=640, conf=0.20, verbose=False, stream=True)):
        if len(r.boxes) == 0:
            print(m, "terlewat:", os.path.basename(p))
