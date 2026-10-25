import glob, os
from PIL import Image
from ultralytics import YOLO

def foto(folder):
    return sorted(f for f in glob.glob(os.path.join(folder, "*"))
                  if f.lower().endswith((".jpg", ".jpeg", ".png")))
def berkotak(f):
    t = os.path.splitext(f)[0] + ".txt"
    return os.path.exists(t) and os.path.getsize(t) > 0

api = [f for f in foto("foto_cam/camA_layar_val") if berkotak(f)]
os.makedirs("pad_foto", exist_ok=True)
pad = []
for f in api:
    im = Image.open(f).convert("RGB").resize((640, 480))
    kanvas = Image.new("RGB", (640, 640), (114, 114, 114))
    kanvas.paste(im, (0, 80))
    out = os.path.join("pad_foto", os.path.basename(f))
    kanvas.save(out, quality=95)
    pad.append(out)

def skor(model, files):
    return [max((float(b.conf) for b in r.boxes), default=0.0)
            for r in model.predict(files, imgsz=640, conf=0.03, verbose=False, stream=True)]

pt = YOLO("best_v3.pt")
nc = YOLO("best_v3_ncnn_model", task="detect")
a = skor(pt, api)
b = skor(pt, pad)
c = skor(nc, api)
print("foto  pt_asli  pt_dipad  ncnn")
for f, x, y, z in zip(api, a, b, c):
    print(os.path.basename(f)[:20], round(x, 2), round(y, 2), round(z, 2))
for nama, s in (("pt_asli", a), ("pt_dipad", b), ("ncnn", c)):
    print(nama, "terdeteksi di 0.20:", sum(v >= 0.20 for v in s), "/", len(s))
