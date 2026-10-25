import os
from ultralytics import YOLO
F = ["foto_tes3/api/caleb-cook-syuox8fipX4-unsplash.jpg",
     "foto_tes3/api/jeromey-balderrama-UgONGONhhls-unsplash.jpg"]
for m in ("best_v3.pt", "best_v4.pt"):
    mod = YOLO(m)
    for sz in (640, 960, 1280):
        for f in F:
            r = mod.predict(f, imgsz=sz, conf=0.03, verbose=False)[0]
            s = max((float(b.conf) for b in r.boxes), default=0.0)
            print(m, sz, os.path.basename(f)[:10], "skor tertinggi:", round(s, 2))
