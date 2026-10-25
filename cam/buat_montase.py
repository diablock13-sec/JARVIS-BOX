import glob, os, sys
import cv2
import numpy as np

root = os.path.expanduser("~/JARVIS-BOX/foto_cam")
folders = sys.argv[1:] or ["camA_layar_train", "camA_layar_val"]
W, H, KOL, PER = 320, 240, 5, 20

def label_kosong(jpg):
    txt = os.path.splitext(jpg)[0] + ".txt"
    if not os.path.exists(txt):
        return True
    with open(txt) as f:
        return not f.read().strip()

kosong = []
for fo in folders:
    for f in sorted(glob.glob(os.path.join(root, fo, "*.jpg"))):
        if label_kosong(f):
            kosong.append(f)

print(f"{len(kosong)} foto tanpa kotak")
for f in kosong:
    print("  ", os.path.relpath(f, root))

for halaman, mulai in enumerate(range(0, len(kosong), PER), 1):
    grup = kosong[mulai:mulai + PER]
    baris = []
    for i in range(0, len(grup), KOL):
        sel = []
        for f in grup[i:i + KOL]:
            im = cv2.imread(f)
            if im is None:
                im = np.zeros((H, W, 3), np.uint8)
            else:
                im = cv2.resize(im, (W, H))
            tag = "T" if "train" in os.path.basename(os.path.dirname(f)) else "V"
            nama = os.path.basename(f).replace("layar_src_", "").replace(".jpg", "")
            cv2.rectangle(im, (0, 0), (W, 22), (0, 0, 0), -1)
            cv2.putText(im, f"{tag} {nama}", (4, 16), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            sel.append(im)
        while len(sel) < KOL:
            sel.append(np.zeros((H, W, 3), np.uint8))
        baris.append(np.hstack(sel))
    out = os.path.expanduser(f"~/JARVIS-BOX/montase_tanpa_kotak_{halaman}.jpg")
    cv2.imwrite(out, np.vstack(baris))
    print("tersimpan:", out)
