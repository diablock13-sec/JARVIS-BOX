import glob, os, sys, time
from PIL import Image
from ultralytics import YOLO

os.makedirs("bench_foto", exist_ok=True)
files = []
for f in sorted(glob.glob("foto_tes3/api/*.jpg"))[:20]:
    out = os.path.join("bench_foto", os.path.basename(f))
    if not os.path.exists(out):
        Image.open(f).convert("RGB").resize((640, 480)).save(out, quality=90)
    files.append(out)

for nama in sys.argv[1:]:
    m = YOLO(nama, task="detect")
    m.predict(files[0], imgsz=640, conf=0.2, verbose=False)   # pemanasan
    t = time.time()
    for f in files:
        m.predict(f, imgsz=640, conf=0.2, verbose=False)
    print(nama, round((time.time() - t) / len(files) * 1000), "ms per frame 640x480")
