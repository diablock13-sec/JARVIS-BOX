import csv, glob, os, re, shutil, sys
from datetime import datetime, timedelta

PILIH = sys.argv[1:]          # kosong = semua uji di hasil_uji_cepat.txt
FMT = "%Y-%m-%dT%H:%M:%S"
def dt(s): return datetime.strptime(s, FMT)

txt = open("hasil_uji_cepat.txt", encoding="utf-8").read()
jendela = re.findall(r"== (\S+) \| (\S+) sampai (\S+) ==", txt)
if PILIH:
    jendela = [j for j in jendela if j[0] in PILIH]
if not jendela:
    sys.exit("Tidak ada jendela uji yang cocok")

baris = []
with open("hasil_box/log.csv", newline="", encoding="utf-8") as f:
    for r in csv.DictReader(f):
        if r.get("status") not in (None, "status"):
            baris.append(r)

def angka(x):
    try: return float(x)
    except (TypeError, ValueError): return None
def maks(rs, k):
    v = [angka(r[k]) for r in rs if angka(r[k]) is not None]
    return max(v) if v else None
def rata(rs, k):
    v = [angka(r[k]) for r in rs if angka(r[k]) is not None]
    return sum(v) / len(v) if v else None

def iso_foto(nama):
    m = re.search(r"alarm_(\d{8})_(\d{6})", nama)
    if not m: return None
    d, t = m.groups()
    return f"{d[:4]}-{d[4:6]}-{d[6:]}T{t[:2]}:{t[2:4]}:{t[4:]}"

foto = sorted(glob.glob("hasil_box/alarm_*.jpg"))
os.makedirs("per_uji", exist_ok=True)
terpakai = set()
hasil = []

for nama, a, b in jendela:
    tujuan = os.path.join("per_uji", nama)
    os.makedirs(tujuan, exist_ok=True)
    sub = [r for r in baris if a <= r["waktu"] <= b]
    with open(os.path.join(tujuan, "log_" + nama + ".csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=sub[0].keys() if sub else ["waktu"])
        w.writeheader(); w.writerows(sub)
    hit = {}
    for r in sub: hit[r["status"]] = hit.get(r["status"], 0) + 1
    alarm = [r["waktu"] for r in sub if r["status"] == "ALARM"]
    n_foto = 0
    for f in foto:
        iso = iso_foto(f)
        if iso and a <= iso <= b:
            shutil.copy(f, tujuan); terpakai.add(f); n_foto += 1
    hasil.append({
        "uji": nama, "mulai": a, "selesai": b,
        "lama_detik": int((dt(b) - dt(a)).total_seconds()),
        "siklus": len(sub),
        "aman": hit.get("aman", 0), "deteksi": hit.get("deteksi", 0),
        "alarm": hit.get("ALARM", 0), "frame_gagal": hit.get("frame_gagal", 0),
        "fire_maks": maks(sub, "fire"), "smoke_maks": maks(sub, "smoke"),
        "kotak_maks": maks(sub, "kotak"), "ms_rata": rata(sub, "ms"),
        "suhu_maks": maks(sub, "suhu"),
        "alarm_pertama": alarm[0] if alarm else "",
        "detik_dari_mulai": int((dt(alarm[0]) - dt(a)).total_seconds()) if alarm else "",
        "foto_alarm": n_foto,
    })

# foto alarm di luar jendela terpilih tetapi dekat waktu uji: kemungkinan sisa deteksi
lo = min(dt(j[1]) for j in jendela) - timedelta(minutes=2)
hi = max(dt(j[2]) for j in jendela) + timedelta(minutes=10)
os.makedirs("di_luar_jendela", exist_ok=True)
sisa = []
for f in foto:
    iso = iso_foto(f)
    if iso and f not in terpakai and lo <= dt(iso) <= hi:
        shutil.copy(f, "di_luar_jendela"); sisa.append(os.path.basename(f))

with open("ringkasan_uji.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(hasil[0].keys()))
    w.writeheader(); w.writerows(hasil)

for h in hasil:
    print({k: (round(v, 2) if isinstance(v, float) else v) for k, v in h.items()})
print("\nFoto alarm di luar jendela (dekat waktu uji):", sisa if sisa else "tidak ada")
