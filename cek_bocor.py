from pathlib import Path
import re, hashlib, random

ROOT = Path.home() / "JARVIS-BOX" / "dataset"
EXT = {".jpg", ".jpeg", ".png"}
dasar = lambda n: re.split(r"\.rf\.", n)[0]

def peta(split):
    d = {}
    for p in (ROOT / split / "images").iterdir():
        if p.suffix.lower() in EXT:
            d.setdefault(dasar(p.name), []).append(p)
    return d

tr, va, te = peta("train"), peta("valid"), peta("test")
random.seed(1)

bersama = sorted(set(tr) & set(va))
print("Contoh nama yang sama di train dan valid:")
for k in random.sample(bersama, min(5, len(bersama))):
    print(" ", k, "| train:", len(tr[k]), "salinan | valid:", len(va[k]), "salinan")

def md5(p):
    return hashlib.md5(p.read_bytes()).hexdigest()

dua = sorted(set(va) & set(te))
identik = sum(1 for k in dua if {md5(p) for p in va[k]} & {md5(p) for p in te[k]})
print(f"\nvalid vs test: {len(dua)} nama sama, {identik} di antaranya file identik (isi byte sama)")

print("\nBandingkan 3 pasangan ini secara visual di file manager:")
for k in random.sample(bersama, min(3, len(bersama))):
    print(" ", tr[k][0])
    print(" ", va[k][0])
    print()
