import sys
from pathlib import Path
from ultralytics import YOLO
m = YOLO("best_v3.pt")
out = Path("pra_label_cek"); out.mkdir(exist_ok=True)
for sesi in sys.argv[1:]:
    for f in sorted(Path("foto_cam", sesi).glob("*.jpg")):
        r = m.predict(str(f), imgsz=640, conf=0.10, verbose=False)[0]
        lines = [f"{int(b.cls)} " + " ".join(f"{v:.6f}" for v in b.xywhn[0].tolist()) for b in r.boxes]
        f.with_suffix(".txt").write_text("\n".join(lines) + ("\n" if lines else ""))
        r.save(filename=str(out / f"{sesi}_{f.name}"))
        print(f"{sesi}/{f.name}: {len(lines)} kotak")
