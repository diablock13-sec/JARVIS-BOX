import os
from PIL import Image
from ultralytics import YOLO
src = "foto_tes3/api/jeromey-balderrama-UgONGONhhls-unsplash.jpg"
im = Image.open(src).convert("RGB")
im = im.resize((640, int(640 * im.height / im.width)))
im.save("jeromey_640.jpg", quality=90)
for m in ("best_v3.pt", "best_v4.pt"):
    mod = YOLO(m)
    for sz in (640, 1280):
        r = mod.predict("jeromey_640.jpg", imgsz=sz, conf=0.03, verbose=False)[0]
        s = max((float(b.conf) for b in r.boxes), default=0.0)
        print(m, sz, "skor tertinggi:", round(s, 2))
