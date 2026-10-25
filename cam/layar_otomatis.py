import argparse, time, urllib.request
from pathlib import Path
import cv2, numpy as np

ap = argparse.ArgumentParser()
ap.add_argument("sesi", choices=["train", "val"])
ap.add_argument("--ip", default="10.42.0.21")
ap.add_argument("--tunggu", type=float, default=2.5, help="detik gambar tampil sebelum difoto")
ap.add_argument("--lebar", type=int, default=1920)
ap.add_argument("--tinggi", type=int, default=1080)
a = ap.parse_args()

src = sorted(p for p in Path("sumber_layar", a.sesi).iterdir()
             if p.suffix.lower() in {".jpg", ".jpeg", ".png"})
out = Path("foto_cam", f"camA_layar_{a.sesi}"); out.mkdir(parents=True, exist_ok=True)

def ambil(path):
    data = urllib.request.urlopen(f"http://{a.ip}/capture", timeout=5).read()
    Path(path).write_bytes(data)

win = "layar"
cv2.namedWindow(win, cv2.WND_PROP_FULLSCREEN)
cv2.setWindowProperty(win, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
W, H = a.lebar, a.tinggi
w43 = int(H * 4 / 3)

def kanvas(img):
    h, w = img.shape[:2]
    if w / h > 4 / 3:
        nw = int(h * 4 / 3); x0 = (w - nw) // 2; img = img[:, x0:x0 + nw]
    else:
        nh = int(w * 3 / 4); y0 = (h - nh) // 2; img = img[y0:y0 + nh, :]
    img = cv2.resize(img, (w43, H))
    c = np.zeros((H, W, 3), np.uint8)
    x = (W - w43) // 2
    c[:, x:x + w43] = img
    return c

n = 0
for p in src:
    f1, f2 = out / f"layar_{p.stem}_f1.jpg", out / f"layar_{p.stem}_f2.jpg"
    if f1.exists() and f2.exists():
        continue
    img = cv2.imread(str(p))
    if img is None:
        print("gagal baca", p); continue
    cv2.imshow(win, kanvas(img))
    if cv2.waitKey(int(a.tunggu * 1000)) & 0xFF == ord("q"):
        break
    try:
        ambil(out / "_pemanasan.tmp"); time.sleep(0.3)
        ambil(f1); time.sleep(0.5); ambil(f2)
        n += 1
        print(f"{p.name}: 2 frame ({n} selesai dari {len(src)})")
    except Exception as e:
        print(f"{p.name}: GAGAL ({e})")
cv2.destroyAllWindows()
(out / "_pemanasan.tmp").unlink(missing_ok=True)
print("Selesai. File:", len(list(out.glob("*.jpg"))))
