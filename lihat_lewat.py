import os
from ultralytics import YOLO
F = ["foto_tes3/api/caleb-cook-syuox8fipX4-unsplash.jpg",
     "foto_tes3/api/jeromey-balderrama-UgONGONhhls-unsplash.jpg"]
os.makedirs("cek_lewat", exist_ok=True)
for m in ("best_v3.pt", "best_v4.pt"):
    mod = YOLO(m)
    for f in F:
        r = mod.predict(f, imgsz=640, conf=0.03, verbose=False)[0]
        skor = [(mod.names[int(b.cls)], round(float(b.conf), 2)) for b in r.boxes]
        print(m, os.path.basename(f)[:12], skor if skor else "tidak ada deteksi")
        r.save(filename=f"cek_lewat/{m[:-3]}_{os.path.basename(f)}")
