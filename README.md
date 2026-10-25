# JARVIS: deteksi dini kebakaran hutan dan lahan

Prototipe yang masih dikerjakan. Tujuannya perangkat portabel deteksi dini
kebakaran (mendukung SDG 15 dan SDG 13) dengan kamera, model YOLO, sensor,
dan notifikasi.

## Status

| Bagian | Status |
| --- | --- |
| Deteksi api dan asap (YOLO11n, kelas Fire dan Smoke) | berjalan |
| ESP32-CAM mengirim foto lewat WiFi | berjalan, stabilitas sambungan masih diuji |
| Raspberry Pi 3B+ menjalankan deteksi (NCNN), alarm setelah 3 siklus berturut-turut | berjalan |
| Sensor gas (MQ-2), suhu dan kelembapan (DHT11) | belum |
| GPS, LoRa SX1278, SIM7600E, notifikasi Telegram | belum |
| Drone | belum |

## Isi repo

Skrip pengambilan foto, pelabelan, evaluasi, dan deteksi. Sketch kamera ada di
`cam_contoh/` dengan sandi WiFi diganti placeholder.

Tidak termasuk: dataset, foto, berkas model (.pt), dan sandi.

## Data

Dataset awal: Roboflow "fire-smoke-detection-yolov11" versi 2 (CC BY 4.0).
Foto negatif dan foto kamera tambahan dibuat sendiri dan tidak dibagikan.
