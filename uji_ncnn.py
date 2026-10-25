import glob, os
from ultralytics import YOLO

MODELS = ["best_v3.pt", "best_v3_ncnn_model"]
CONFS = [0.20]
EXT = (".jpg", ".jpeg", ".png")

def foto(folder):
    return sorted(f for f in glob.glob(os.path.join(folder, "*"))
                  if f.lower().endswith(EXT))

def berkotak(f):
    t = os.path.splitext(f)[0] + ".txt"
    return os.path.exists(t) and os.path.getsize(t) > 0

layar = foto("foto_cam/camA_layar_val")
grup = {
    "tes3/api":        ("pos", foto("foto_tes3/api")),
    "tes3/bukan_api":  ("neg", foto("foto_tes3/bukan_api")),
    "tes3/abu_abu":    ("abu", foto("foto_tes3/abu_abu")),
    "camA_val":        ("neg", foto("foto_cam/camA_val")),
    "layar_val/api":   ("pos", [f for f in layar if berkotak(f)]),
    "layar_val/negatif": ("neg", [f for f in layar if not berkotak(f)]),
}
print({k: len(v[1]) for k, v in grup.items()})

for m in MODELS:
    model = YOLO(m)
    for c in CONFS:
        print(f"\n== {m}  conf={c} ==")
        for nama, (jenis, files) in grup.items():
            if not files:
                continue
            ada = [len(r.boxes) > 0 for r in
                   model.predict(files, imgsz=640, conf=c, verbose=False, stream=True)]
            n = sum(ada)
            ket = {"pos": "terdeteksi (recall)", "neg": "salah deteksi", "abu": "terdeteksi (dipantau)"}[jenis]
            print(f"{nama:20s} {n:3d}/{len(files):<3d} {ket}")
            if jenis == "neg" and n:
                print("   salah deteksi:", [os.path.basename(f) for f, a in zip(files, ada) if a])
