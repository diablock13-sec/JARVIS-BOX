import glob, os
from ultralytics import YOLO

def foto(folder):
    return sorted(f for f in glob.glob(os.path.join(folder, "*"))
                  if f.lower().endswith((".jpg", ".jpeg", ".png")))
def berkotak(f):
    t = os.path.splitext(f)[0] + ".txt"
    return os.path.exists(t) and os.path.getsize(t) > 0

layar = foto("foto_cam/camA_layar_val")
grup = {
    "layar api": [f for f in layar if berkotak(f)],
    "layar negatif": [f for f in layar if not berkotak(f)],
    "camA_val": foto("foto_cam/camA_val"),
}
pt = YOLO("best_v3.pt")
nc = YOLO("best_v3_ncnn_model", task="detect")
for nama, mdl, sz in (("pt", pt, 640), ("ncnn_480x640", nc, [480, 640])):
    for c in (0.20, 0.10):
        for g, files in grup.items():
            n = sum(len(r.boxes) > 0 for r in
                    mdl.predict(files, imgsz=sz, conf=c, verbose=False, stream=True))
            print(nama, c, g, f"{n}/{len(files)}")
