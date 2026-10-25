import sys
from pathlib import Path
import cv2, numpy as np

AMBANG = 5   # jarak hash maksimum dianggap kembar
def dhash(p):
    g = cv2.cvtColor(cv2.imread(str(p)), cv2.COLOR_BGR2GRAY)
    g = cv2.resize(g, (9, 8), interpolation=cv2.INTER_AREA)
    return (g[:, 1:] > g[:, :-1]).flatten()

fs = [(p, s) for s in ("train", "val") for p in sorted(Path("sumber_layar", s).glob("*.jpg"))]
h = {p: dhash(p) for p, _ in fs}
split = dict(fs)
induk = {p: p for p, _ in fs}
def cari(x):
    while induk[x] != x: x = induk[x]
    return x
for i, (p, _) in enumerate(fs):
    for q, _ in fs[i + 1:]:
        if int((h[p] != h[q]).sum()) <= AMBANG:
            induk[cari(q)] = cari(p)
grup = {}
for p, _ in fs: grup.setdefault(cari(p), []).append(p)
buang = []
for g in grup.values():
    if len(g) < 2: continue
    # simpan satu; utamakan yang di val supaya val tetap terisi
    g = sorted(g, key=lambda p: (split[p] != "val", str(p)))
    print("kembar:", [f"{split[p]}/{p.name}" for p in g], "-> simpan", f"{split[g[0]]}/{g[0].name}")
    buang += g[1:]
print(f"\n{len(buang)} file akan dibuang dari {len(fs)}.")
if "--hapus" in sys.argv:
    for p in buang: p.unlink()
    for s in ("train", "val"):
        print(s, len(list(Path("sumber_layar", s).glob("*.jpg"))), "file")
else:
    print("Pratinjau saja. Tambahkan --hapus untuk menghapus.")
