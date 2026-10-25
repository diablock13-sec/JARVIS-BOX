/*
  jarvis_cam.ino
  Kamera A JARVIS (ESP32-CAM, sensor GC2145) untuk jaringan hotspot Raspberry Pi.

  Fungsi:
    GET /capture                       -> satu frame JPEG 640x480
    GET /status                        -> info singkat (sensor, sinyal, memori, waktu hidup)
    GET /set?vflip=1&hmirror=0         -> ubah orientasi saat jalan (tanpa unggah ulang)
    GET /                              -> halaman teks sederhana

  Jaringan:
    SSID "JARVIS-CAM" (hotspot di Pi), IP tetap 10.77.77.20, gateway 10.77.77.1.
    Menyambung ulang sendiri bila WiFi putus; restart bila putus lebih dari 2 menit.

  Catatan penting:
    - Sketch lama sudah tidak ada, jadi pin memakai peta AI-Thinker ESP32-CAM.
      Kalau papanmu bukan AI-Thinker, kamera gagal dimulai dan Serial Monitor menampilkan
      "esp_camera_init gagal". Saat itu ganti blok pin di bawah.
    - Orientasi awal: tanpa flip dan tanpa mirror. Cek hasil /capture, lalu setel dengan
      /set?vflip=1&hmirror=1 sampai benar, dan salin nilainya ke FLIP_VERTICAL dan
      MIRROR_HORIZONTAL di bawah. Nilai di /set hilang saat kamera restart.
    - GC2145 tidak punya encoder JPEG, jadi frame diambil RGB565 lalu diubah ke JPEG.
      Ini butuh PSRAM. Di Arduino IDE pilih papan "AI Thinker ESP32-CAM" (PSRAM aktif),
      atau "ESP32 Wrover Module" dengan PSRAM "Enabled". Core ESP32 versi 2.x atau 3.x.
    - Isi WIFI_PASS langsung di Arduino IDE. Jangan menulis sandi di chat.
*/

#include "esp_camera.h"
#include "img_converters.h"
#include <WiFi.h>
#include <WebServer.h>

// ===================== PENGATURAN =====================
const char* WIFI_SSID = "JARVIS-CAM2";
const char* WIFI_PASS = "GANTI_DENGAN_SANDI";

IPAddress IP_KAMERA(10, 77, 77, 20);
IPAddress IP_GATEWAY(10, 77, 77, 1);
IPAddress IP_MASK(255, 255, 255, 0);
IPAddress IP_DNS(10, 77, 77, 1);

const bool FLIP_VERTICAL     = false;    // setel setelah melihat hasil /capture
const bool MIRROR_HORIZONTAL = false;    // setel setelah melihat hasil /capture
const int  JPEG_QUALITY      = 80;       // 0 sampai 100, makin besar makin bagus dan makin besar berkasnya
const int  XCLK_HZ           = 20000000; // turunkan ke 10000000 bila frame sering gagal
const unsigned long RESTART_BILA_PUTUS_MS = 120000;

// ===================== PIN AI-THINKER ESP32-CAM =====================
#define PWDN_GPIO_NUM   32
#define RESET_GPIO_NUM  -1
#define XCLK_GPIO_NUM    0
#define SIOD_GPIO_NUM   26
#define SIOC_GPIO_NUM   27
#define Y9_GPIO_NUM     35
#define Y8_GPIO_NUM     34
#define Y7_GPIO_NUM     39
#define Y6_GPIO_NUM     36
#define Y5_GPIO_NUM     21
#define Y4_GPIO_NUM     19
#define Y3_GPIO_NUM     18
#define Y2_GPIO_NUM      5
#define VSYNC_GPIO_NUM  25
#define HREF_GPIO_NUM   23
#define PCLK_GPIO_NUM   22

WebServer server(80);
uint16_t sensorPID = 0;
unsigned long terputusSejak = 0;
unsigned long cekTerakhir = 0;

bool mulaiKamera() {
  if (!psramFound()) {
    Serial.println("PSRAM tidak ditemukan. RGB565 640x480 butuh PSRAM.");
    return false;
  }

  camera_config_t c = {};
  c.ledc_channel = LEDC_CHANNEL_0;
  c.ledc_timer   = LEDC_TIMER_0;
  c.pin_d0 = Y2_GPIO_NUM;
  c.pin_d1 = Y3_GPIO_NUM;
  c.pin_d2 = Y4_GPIO_NUM;
  c.pin_d3 = Y5_GPIO_NUM;
  c.pin_d4 = Y6_GPIO_NUM;
  c.pin_d5 = Y7_GPIO_NUM;
  c.pin_d6 = Y8_GPIO_NUM;
  c.pin_d7 = Y9_GPIO_NUM;
  c.pin_xclk  = XCLK_GPIO_NUM;
  c.pin_pclk  = PCLK_GPIO_NUM;
  c.pin_vsync = VSYNC_GPIO_NUM;
  c.pin_href  = HREF_GPIO_NUM;
  c.pin_sscb_sda = SIOD_GPIO_NUM;
  c.pin_sscb_scl = SIOC_GPIO_NUM;
  c.pin_pwdn  = PWDN_GPIO_NUM;
  c.pin_reset = RESET_GPIO_NUM;
  c.xclk_freq_hz = XCLK_HZ;
  c.pixel_format = PIXFORMAT_RGB565;
  c.frame_size   = FRAMESIZE_VGA;      // 640x480
  c.jpeg_quality = 12;                 // tidak dipakai pada RGB565
  c.fb_count     = 1;
  c.fb_location  = CAMERA_FB_IN_PSRAM;
  c.grab_mode    = CAMERA_GRAB_WHEN_EMPTY;

  esp_err_t err = esp_camera_init(&c);
  if (err != ESP_OK) {
    Serial.printf("esp_camera_init gagal: 0x%x\n", err);
    return false;
  }

  sensor_t* s = esp_camera_sensor_get();
  if (s) {
    sensorPID = s->id.PID;
    Serial.printf("Sensor PID: 0x%04X (GC2145 = 0x2145)\n", sensorPID);
    s->set_vflip(s, FLIP_VERTICAL ? 1 : 0);
    s->set_hmirror(s, MIRROR_HORIZONTAL ? 1 : 0);
  }
  return true;
}

void sambungWiFi() {
  WiFi.mode(WIFI_STA);
  WiFi.persistent(false);
  WiFi.setAutoReconnect(true);
  WiFi.setSleep(false);
  WiFi.config(IP_KAMERA, IP_GATEWAY, IP_MASK, IP_DNS);
  WiFi.begin(WIFI_SSID, WIFI_PASS);

  Serial.printf("Menyambung ke %s ", WIFI_SSID);
  unsigned long mulai = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - mulai < 20000) {
    delay(500);
    Serial.print(".");
  }
  Serial.println();
  if (WiFi.status() == WL_CONNECTED) {
    Serial.print("Tersambung. IP: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("Belum tersambung. Akan dicoba lagi di loop.");
  }
}

void tanganiCapture() {
  // Buang satu frame lama supaya yang dikirim adalah frame yang baru.
  camera_fb_t* fb = esp_camera_fb_get();
  if (fb) esp_camera_fb_return(fb);

  fb = esp_camera_fb_get();
  if (!fb) {
    server.send(503, "text/plain", "kamera gagal mengambil frame");
    return;
  }

  uint8_t* jpg = nullptr;
  size_t jpgLen = 0;
  bool ok = frame2jpg(fb, JPEG_QUALITY, &jpg, &jpgLen);
  esp_camera_fb_return(fb);

  if (!ok || !jpg) {
    server.send(500, "text/plain", "gagal mengubah frame ke JPEG");
    return;
  }

  server.sendHeader("Cache-Control", "no-store");
  server.sendHeader("Connection", "close");
  server.setContentLength(jpgLen);
  server.send(200, "image/jpeg", "");
  server.client().write((const char*)jpg, jpgLen);
  free(jpg);
}

void tanganiSet() {
  sensor_t* s = esp_camera_sensor_get();
  if (!s) {
    server.send(500, "text/plain", "sensor tidak ada");
    return;
  }
  if (server.hasArg("vflip"))   s->set_vflip(s, server.arg("vflip").toInt() ? 1 : 0);
  if (server.hasArg("hmirror")) s->set_hmirror(s, server.arg("hmirror").toInt() ? 1 : 0);
  server.send(200, "text/plain", "ok");
}

void tanganiStatus() {
  String t = "{";
  t += "\"sensor_pid\":\"0x";
  t += String(sensorPID, HEX);
  t += "\",\"ip\":\"";
  t += WiFi.localIP().toString();
  t += "\",\"rssi\":";
  t += String(WiFi.RSSI());
  t += ",\"heap_bebas\":";
  t += String(ESP.getFreeHeap());
  t += ",\"psram_bebas\":";
  t += String(ESP.getFreePsram());
  t += ",\"hidup_detik\":";
  t += String(millis() / 1000);
  t += "}";
  server.send(200, "application/json", t);
}

void tanganiRoot() {
  String t = "Kamera A JARVIS\n";
  t += "GET /capture  -> JPEG 640x480\n";
  t += "GET /status   -> info\n";
  t += "GET /set?vflip=1&hmirror=0 -> orientasi\n";
  server.send(200, "text/plain", t);
}

void setup() {
  Serial.begin(115200);
  delay(500);
  Serial.println();
  Serial.println("Kamera A JARVIS mulai");

  if (!mulaiKamera()) {
    Serial.println("Kamera gagal dimulai. Restart dalam 5 detik.");
    delay(5000);
    ESP.restart();
  }

  sambungWiFi();

  server.on("/", tanganiRoot);
  server.on("/capture", tanganiCapture);
  server.on("/status", tanganiStatus);
  server.on("/set", tanganiSet);
  server.begin();
  Serial.println("Server HTTP aktif di port 80");
}

void loop() {
  server.handleClient();

  if (millis() - cekTerakhir > 5000) {
    cekTerakhir = millis();
    if (WiFi.status() == WL_CONNECTED) {
      terputusSejak = 0;
    } else {
      if (terputusSejak == 0) terputusSejak = millis();
      Serial.println("WiFi putus, mencoba menyambung ulang");
      WiFi.reconnect();
      if (millis() - terputusSejak > RESTART_BILA_PUTUS_MS) {
        Serial.println("Putus terlalu lama. Restart.");
        ESP.restart();
      }
    }
  }
}
