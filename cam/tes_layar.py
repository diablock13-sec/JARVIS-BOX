import argparse, time, urllib.request
import cv2, numpy as np

def pola(W, H):
    w43 = int(H * 4 / 3); x0 = (W - w43) // 2
    c = np.zeros((H, W, 3), np.uint8)
    c[:, x0:x0 + w43] = 255
    for i in range(1, 8):
        cv2.line(c, (x0 + i * w43 // 8, 0), (x0 + i * w43 // 8, H), (0, 0, 0), 3)
        cv2.line(c, (x0, i * H // 8), (x0 + w43, i * H // 8), (0, 0, 0), 3)
    cv2.putText(c, "TES POSISI KAMERA", (x0 + w43 // 2 - 260, H // 2 - 20),
                cv2.FONT_HERSHEY_SIMPLEX, 1.6, (0, 0, 255), 4)
    return c

def analisis(img):
    h, w = img.shape[:2]
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, m = cv2.threshold(g, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((25, 25), np.uint8))
    cs, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not cs:
        return None, ["Pola tidak terdeteksi. Pastikan kamera menghadap layar."]
    c = max(cs, key=cv2.contourArea)
    x, y, bw, bh = cv2.boundingRect(c)
    (_, _), _, ang = cv2.minAreaRect(c)
    ang = ang % 90; ang = ang - 90 if ang > 45 else ang
    sak = []
    cov = max(bw / w, bh / h)
    dx, dy = (x + bw / 2 - w / 2) / w, (y + bh / 2 - h / 2) / h
    if x <= 2 or y <= 2 or x + bw >= w - 2 or y + bh >= h - 2:
        sak.append("Pola menyentuh tepi bingkai: kamera terlalu dekat, mundurkan sedikit.")
    elif cov < 0.88:
        sak.append(f"Pola baru {cov*100:.0f}% bingkai: dekatkan kamera.")
    if abs(dx) > 0.04:
        s = "kanan" if dx > 0 else "kiri"
        sak.append(f"Pola terlalu ke {s}: arahkan kamera sedikit ke {s}.")
    if abs(dy) > 0.04:
        s = "bawah" if dy > 0 else "atas"
        sak.append(f"Pola terlalu ke {s}: arahkan kamera sedikit ke {s}.")
    if abs(ang) > 3:
        sak.append(f"Kamera miring {ang:.1f} derajat: putar badan kamera sampai lurus.")
    tajam = cv2.Laplacian(g[h // 4:3 * h // 4, w // 4:3 * w // 4], cv2.CV_64F).var()
    if not sak:
        sak.append("POSISI BAGUS.")
    sak.append(f"Ketajaman {tajam:.0f} (bandingkan hanya pada jarak yang sama; makin besar makin tajam).")
    return (x, y, bw, bh), sak

ap = argparse.ArgumentParser()
ap.add_argument("--ip", default="10.42.0.21")
ap.add_argument("--lebar", type=int, default=1920)
ap.add_argument("--tinggi", type=int, default=1080)
ap.add_argument("--tunggu", type=float, default=3.0)
a = ap.parse_args()
win = "tes"
cv2.namedWindow(win, cv2.WND_PROP_FULLSCREEN)
cv2.setWindowProperty(win, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
P = pola(a.lebar, a.tinggi)
while True:
    cv2.imshow(win, P); cv2.waitKey(int(a.tunggu * 1000))
    try:
        for _ in range(2):
            d = urllib.request.urlopen(f"http://{a.ip}/capture", timeout=5).read()
            time.sleep(0.3)
        img = cv2.imdecode(np.frombuffer(d, np.uint8), cv2.IMREAD_COLOR)
    except Exception as e:
        print("Gagal ambil foto:", e); break
    box, sak = analisis(img)
    out = img.copy()
    if box:
        x, y, bw, bh = box
        cv2.rectangle(out, (x, y), (x + bw, y + bh), (0, 255, 0), 2)
    h, w = out.shape[:2]
    cv2.line(out, (w // 2, 0), (w // 2, h), (255, 0, 0), 1)
    cv2.line(out, (0, h // 2), (w, h // 2), (255, 0, 0), 1)
    cv2.imwrite("tes_posisi.jpg", out)
    print("\n".join(sak)); print("-" * 40)
    canvas = np.zeros((a.tinggi, a.lebar, 3), np.uint8)
    s = min(a.lebar / w, (a.tinggi - 200) / h)
    im2 = cv2.resize(out, None, fx=s, fy=s)
    canvas[:im2.shape[0], :im2.shape[1]] = im2
    for i, t in enumerate(sak):
        cv2.putText(canvas, t, (20, im2.shape[0] + 45 + i * 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
    cv2.putText(canvas, "SPASI = tes lagi   Q = selesai", (20, a.tinggi - 15),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
    cv2.imshow(win, canvas)
    if cv2.waitKey(0) & 0xFF == ord("q"):
        break
cv2.destroyAllWindows()
