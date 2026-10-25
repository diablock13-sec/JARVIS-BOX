#include <WiFi.h>
#include <WebServer.h>
#include "DHT.h"

#define DHTPIN 4
#define DHTTYPE DHT11

const char* WIFI_SSID = "NAMA_WIFI";
const char* WIFI_PASS = "GANTI_DENGAN_SANDI";

// Ambang (ubah sesuai tahap uji)
const float SUHU_BATAS   = 28.0;  // °C
const float LEMBAP_BATAS = 60.0;  // %

DHT dht(DHTPIN, DHTTYPE);
WebServer server(80);

float suhu = NAN, lembap = NAN;
bool bahaya = false;
unsigned long terakhirBaca = 0;

void bacaSensor() {
  float h = dht.readHumidity();
  float t = dht.readTemperature();

  if (isnan(h) || isnan(t)) {
    Serial.println("Gagal baca DHT11! Cek kabel/pull-up.");
    return;
  }
  suhu = t;
  lembap = h;
  bahaya = (suhu > SUHU_BATAS && lembap < LEMBAP_BATAS);

  Serial.printf("Suhu: %.1f C | Lembap: %.0f %% | Status: %s\n",
                suhu, lembap, bahaya ? "INDIKASI PANAS!" : "Normal");
}

void halamanUtama() {
  String html = "<!DOCTYPE html><html><head><meta charset='utf-8'>";
  html += "<meta name='viewport' content='width=device-width,initial-scale=1'>";
  html += "<meta http-equiv='refresh' content='2'><title>Jarvis Box</title></head>";
  html += "<body style='font-family:sans-serif;text-align:center;padding:20px;";
  html += bahaya ? "background:#ffd6d6'>" : "background:#e6ffe6'>";
  html += "<h2>Jarvis Box - Monitor</h2>";
  html += "<h1>" + String(suhu, 1) + " &deg;C</h1>";
  html += "<h1>" + String(lembap, 0) + " %</h1>";
  html += "<h3>" + String(bahaya ? "INDIKASI PANAS!" : "Normal") + "</h3>";
  html += "</body></html>";
  server.send(200, "text/html", html);
}

void dataJson() {
  String json = "{\"suhu\":" + String(suhu, 1) +
                ",\"kelembapan\":" + String(lembap, 0) +
                ",\"bahaya\":" + String(bahaya ? "true" : "false") + "}";
  server.send(200, "application/json", json);
}

void setup() {
  Serial.begin(115200);
  dht.begin();

  WiFi.begin(WIFI_SSID, WIFI_PASS);
  Serial.print("Menyambung WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nTersambung! Buka di HP: http://" + WiFi.localIP().toString());

  server.on("/", halamanUtama);
  server.on("/data", dataJson);
  server.begin();
}

void loop() {
  server.handleClient();

  if (millis() - terakhirBaca >= 2000) {  // DHT11 maks ~1x/detik
    terakhirBaca = millis();
    bacaSensor();
  }
}