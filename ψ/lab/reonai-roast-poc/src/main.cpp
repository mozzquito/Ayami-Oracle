// ReonAI Roast POC — dual-thermocouple monitor + optional manual SSR duty
// control, retrofittable onto an existing manual/secondhand coffee roaster.
//
// Scope, on purpose: this POC does NOT do closed-loop/AI roast control yet.
// The open question (per the zcode/agy business review) is whether AI
// control even beats a skilled manual roast — so step one is just to log
// DT/HT/RoR next to a manually-roasted batch and compare, not to automate
// the heater. MONITOR mode (default) never drives the SSR at all. MANUAL_DUTY
// exists only to test that the SSR wiring/switching itself works, at a duty
// cycle a person sets and watches — it is still not automatic temperature
// control. See README.md for the required *hardware* thermal cutoff — this
// firmware's HARD_CUTOFF_C is a software backstop, not a substitute for one.
#include <Arduino.h>
#include <WiFi.h>
#include <LittleFS.h>
#include <ArduinoJson.h>
#include <ESPAsyncWebServer.h>
#include <max6675.h>
#include "secrets.h"

// ---- Pins (ESP32-S3-DevKitC-1) ------------------------------------------
// MAX6675 #1 and #2 share SCK/SO (both are read-only SPI outputs from the
// chip); each gets its own CS. Verify your specific breakout's silkscreen —
// some clones label SO as "DO".
//
// S3-specific: GPIO19/20 are the chip's native USB D-/D+ (used here for the
// serial monitor via ARDUINO_USB_CDC_ON_BOOT) — do NOT reuse them for SPI.
// GPIO0/3/45/46 are boot-strapping pins — avoid. GPIO26-37 are reserved on
// octal-PSRAM S3 modules (varies by board) — avoided here so this works
// whether or not your specific board has PSRAM. GPIO48 is often a WS2812
// RGB status LED (not a plain digitalWrite LED) on S3 DevKitC-1, so the
// fault indicator here uses a separate external LED instead of assuming one.
static const int PIN_SCK = 12;
static const int PIN_SO = 13;
static const int PIN_CS_DT = 14;  // DT probe: bean mass / drum temperature
static const int PIN_CS_HT = 21;  // HT probe: heater temperature
static const int PIN_SSR = 10;    // to the SSR-40DA control input (see README: verify your SSR's minimum trigger voltage before wiring this directly to a 3.3V GPIO)
static const int PIN_FAULT_LED = 11; // external LED + resistor to GND — S3 DevKitC-1's onboard LED is usually addressable RGB (WS2812), not plain on/off

// ---- Safety --------------------------------------------------------------
// Software backstop only. A hardware bimetal/thermal-fuse cutoff in series
// with the heater's mains side, independent of this ESP32, is mandatory
// before this is ever used with a live heater — see README.md "Safety".
static const float HARD_CUTOFF_C = 260.0f;
static const float SSR_PERIOD_MS = 2000.0f; // time-proportioning window

// ---- State -----------------------------------------------------------
enum ControlMode { MODE_MONITOR = 0, MODE_MANUAL_DUTY = 1 };

MAX6675 thermoDT(PIN_SCK, PIN_CS_DT, PIN_SO);
MAX6675 thermoHT(PIN_SCK, PIN_CS_HT, PIN_SO);

AsyncWebServer server(80);
AsyncEventSource events("/api/events");

volatile ControlMode controlMode = MODE_MONITOR;
volatile int manualDutyPercent = 0;
volatile bool fault = false;
String faultReason = "";

float lastDT = NAN, lastHT = NAN;
struct Sample { unsigned long t; float dt; };
static const int ROR_WINDOW = 30; // samples (~30s at 1Hz) for the rate-of-rise slope
Sample rorBuf[ROR_WINDOW];
int rorCount = 0, rorHead = 0;
float lastRoR = 0.0f;

File logFile;
bool logging = false;
String logFileName = "";
unsigned long sessionStartMs = 0;
// Session metadata (set once at "Start logging", repeated on every row) —
// per zcode's review, this is the one thing worth doing before the POC has
// proven anything: keep the log schema clean now so 20-30 real roasts become
// a usable dataset later, without re-flashing firmware to add columns.
String sessionBeanType = "";
String sessionRoastLevel = "";
bool sessionHasSetpoint = false;
float sessionSetpointC = NAN;

// CSV field: strip characters that would break the format instead of quoting,
// since this is a fixed-width sensor log, not general text.
String csvSafe(const String &in) {
  String out = in;
  out.replace(",", " ");
  out.replace("\n", " ");
  out.replace("\r", " ");
  return out;
}

unsigned long lastSampleMs = 0;
static const unsigned long SAMPLE_INTERVAL_MS = 1000;

// ---- Thermocouple reads ------------------------------------------------
// MAX6675 conversion takes ~170-220ms; the Adafruit library blocks for it.
// NaN means "not connected" per the library's own convention — treat it as
// a fault, not as 0°C, so a disconnected probe can never look like a safe
// reading.
float readThermo(MAX6675 &t) {
  float c = t.readCelsius();
  if (isnan(c)) return NAN;
  return c;
}

void updateRoR(unsigned long now, float dt) {
  rorBuf[rorHead] = { now, dt };
  rorHead = (rorHead + 1) % ROR_WINDOW;
  if (rorCount < ROR_WINDOW) rorCount++;
  if (rorCount < 2) { lastRoR = 0.0f; return; }
  int oldestIdx = (rorHead - rorCount + ROR_WINDOW) % ROR_WINDOW;
  Sample oldest = rorBuf[oldestIdx];
  int newestIdx = (rorHead - 1 + ROR_WINDOW) % ROR_WINDOW;
  Sample newest = rorBuf[newestIdx];
  float dtSeconds = (newest.t - oldest.t) / 1000.0f;
  if (dtSeconds < 1.0f) { lastRoR = 0.0f; return; }
  lastRoR = (newest.dt - oldest.dt) / dtSeconds * 60.0f; // deg C per minute
}

void triggerFault(const String &reason) {
  fault = true;
  faultReason = reason;
  controlMode = MODE_MONITOR;
  manualDutyPercent = 0;
  digitalWrite(PIN_SSR, LOW);
  digitalWrite(PIN_FAULT_LED, HIGH);
  Serial.printf("[FAULT] %s\n", reason.c_str());
}

// ---- SSR time-proportioning --------------------------------------------
// Only ever reaches an "on" output when controlMode == MODE_MANUAL_DUTY and
// no fault is latched. MODE_MONITOR always forces the pin LOW.
void serviceSSR() {
  if (fault || controlMode != MODE_MANUAL_DUTY) {
    digitalWrite(PIN_SSR, LOW);
    return;
  }
  unsigned long phase = millis() % (unsigned long)SSR_PERIOD_MS;
  float onTime = (manualDutyPercent / 100.0f) * SSR_PERIOD_MS;
  digitalWrite(PIN_SSR, phase < onTime ? HIGH : LOW);
}

// ---- Logging -----------------------------------------------------------
void startLogging(const String &name, const String &beanType, const String &roastLevel, bool hasSetpoint, float setpointC) {
  if (logging) { logFile.close(); }
  logFileName = "/logs/" + name + ".csv";
  LittleFS.mkdir("/logs");
  logFile = LittleFS.open(logFileName, "w");
  if (!logFile) { Serial.println("[LOG] failed to open file"); return; }
  sessionBeanType = csvSafe(beanType);
  sessionRoastLevel = csvSafe(roastLevel);
  sessionHasSetpoint = hasSetpoint;
  sessionSetpointC = setpointC;
  logFile.println("elapsed_ms,dt_c,ht_c,ror_c_per_min,ssr_duty_pct,mode,bean_type,roast_level,setpoint_c");
  sessionStartMs = millis();
  logging = true;
  Serial.printf("[LOG] started %s (bean=%s roast=%s setpoint=%s)\n",
    logFileName.c_str(), sessionBeanType.c_str(), sessionRoastLevel.c_str(),
    sessionHasSetpoint ? String(sessionSetpointC, 1).c_str() : "none");
}

void stopLogging() {
  if (logging) { logFile.close(); logging = false; Serial.println("[LOG] stopped"); }
}

void appendLogRow(float dt, float ht, float ror) {
  if (!logging || !logFile) return;
  // setpoint_c is session-level (not time-varying) in this POC — there is no
  // closed-loop profile yet, just an optional target the roaster is aiming
  // for by hand. A per-instant setpoint curve is future scope (product item 2).
  logFile.printf("%lu,%.2f,%.2f,%.2f,%d,%d,%s,%s,%s\n",
    millis() - sessionStartMs, dt, ht, ror, manualDutyPercent, (int)controlMode,
    sessionBeanType.c_str(), sessionRoastLevel.c_str(),
    sessionHasSetpoint ? String(sessionSetpointC, 1).c_str() : "");
  logFile.flush();
}

// ---- WiFi ---------------------------------------------------------------
void connectWiFiOrFallbackToAP() {
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  Serial.printf("Connecting to %s", WIFI_SSID);
  unsigned long start = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - start < 12000) {
    delay(300);
    Serial.print(".");
  }
  if (WiFi.status() == WL_CONNECTED) {
    Serial.printf("\nConnected. Dashboard: http://%s/\n", WiFi.localIP().toString().c_str());
    return;
  }
  Serial.println("\nNo WiFi found; starting access point instead.");
  WiFi.mode(WIFI_AP);
  WiFi.softAP("ReonaiRoastPOC", "roastpoc123");
  Serial.printf("AP started. Join \"ReonaiRoastPOC\" (password roastpoc123), dashboard: http://%s/\n",
    WiFi.softAPIP().toString().c_str());
}

// ---- HTTP API ------------------------------------------------------------
void buildStateJson(JsonDocument &doc) {
  if (isnan(lastDT)) doc["dt"] = nullptr; else doc["dt"] = (double)lastDT;
  if (isnan(lastHT)) doc["ht"] = nullptr; else doc["ht"] = (double)lastHT;
  doc["ror"] = lastRoR;
  doc["mode"] = (int)controlMode;
  doc["duty"] = manualDutyPercent;
  doc["fault"] = fault;
  doc["faultReason"] = faultReason;
  doc["logging"] = logging;
  doc["beanType"] = sessionBeanType;
  doc["roastLevel"] = sessionRoastLevel;
  if (sessionHasSetpoint) doc["setpointC"] = (double)sessionSetpointC; else doc["setpointC"] = nullptr;
  doc["uptimeMs"] = millis();
}

void setupRoutes() {
  server.serveStatic("/", LittleFS, "/").setDefaultFile("index.html");

  server.on("/api/state", HTTP_GET, [](AsyncWebServerRequest *req) {
    JsonDocument doc;
    buildStateJson(doc);
    String out;
    serializeJson(doc, out);
    req->send(200, "application/json", out);
  });

  server.on("/api/control", HTTP_POST, [](AsyncWebServerRequest *req) {}, nullptr,
    [](AsyncWebServerRequest *req, uint8_t *data, size_t len, size_t, size_t) {
      JsonDocument doc;
      if (deserializeJson(doc, data, len)) { req->send(400, "text/plain", "bad json"); return; }
      if (fault) { req->send(409, "text/plain", "fault latched; POST /api/reset first"); return; }
      if (doc["mode"].is<int>()) {
        int m = doc["mode"];
        controlMode = (m == 1) ? MODE_MANUAL_DUTY : MODE_MONITOR;
      }
      if (doc["duty"].is<int>()) {
        int d = doc["duty"];
        manualDutyPercent = constrain(d, 0, 100);
      }
      req->send(200, "application/json", "{\"ok\":true}");
    });

  server.on("/api/reset", HTTP_POST, [](AsyncWebServerRequest *req) {
    if (!isnan(lastDT) && lastDT > HARD_CUTOFF_C) { req->send(409, "text/plain", "DT still above cutoff"); return; }
    if (!isnan(lastHT) && lastHT > HARD_CUTOFF_C) { req->send(409, "text/plain", "HT still above cutoff"); return; }
    fault = false; faultReason = "";
    digitalWrite(PIN_FAULT_LED, LOW);
    req->send(200, "application/json", "{\"ok\":true}");
  });

  server.on("/api/log/start", HTTP_POST, [](AsyncWebServerRequest *req) {
    String name = req->hasParam("name") ? req->getParam("name")->value() : String(millis());
    for (size_t i = 0; i < name.length(); i++) if (!isalnum((int)name[i])) name.setCharAt(i, '_');
    String beanType = req->hasParam("bean_type") ? req->getParam("bean_type")->value() : "";
    String roastLevel = req->hasParam("roast_level") ? req->getParam("roast_level")->value() : "";
    bool hasSetpoint = req->hasParam("setpoint_c");
    float setpointC = hasSetpoint ? req->getParam("setpoint_c")->value().toFloat() : NAN;
    startLogging(name, beanType, roastLevel, hasSetpoint, setpointC);
    req->send(200, "application/json", "{\"ok\":true,\"file\":\"" + logFileName + "\"}");
  });

  server.on("/api/log/stop", HTTP_POST, [](AsyncWebServerRequest *req) {
    stopLogging();
    req->send(200, "application/json", "{\"ok\":true}");
  });

  server.on("/api/log/list", HTTP_GET, [](AsyncWebServerRequest *req) {
    JsonDocument doc;
    JsonArray arr = doc.to<JsonArray>();
    File dir = LittleFS.open("/logs");
    if (dir) {
      File f = dir.openNextFile();
      while (f) { arr.add(String(f.name())); f = dir.openNextFile(); }
    }
    String out; serializeJson(doc, out);
    req->send(200, "application/json", out);
  });

  server.on("/api/log/download", HTTP_GET, [](AsyncWebServerRequest *req) {
    if (!req->hasParam("file")) { req->send(400, "text/plain", "missing file param"); return; }
    String path = "/logs/" + req->getParam("file")->value();
    if (!LittleFS.exists(path)) { req->send(404, "text/plain", "not found"); return; }
    req->send(LittleFS, path, "text/csv");
  });

  events.onConnect([](AsyncEventSourceClient *client) {
    if (client->lastId()) Serial.printf("SSE client reconnected, last id %u\n", client->lastId());
  });
  server.addHandler(&events);
}

void setup() {
  Serial.begin(115200);
  pinMode(PIN_SSR, OUTPUT);
  digitalWrite(PIN_SSR, LOW);
  pinMode(PIN_FAULT_LED, OUTPUT);
  digitalWrite(PIN_FAULT_LED, LOW);

  if (!LittleFS.begin(true)) {
    Serial.println("LittleFS mount failed");
  }

  connectWiFiOrFallbackToAP();
  setupRoutes();
  server.begin();
  Serial.println("HTTP server started.");
}

void loop() {
  unsigned long now = millis();

  if (now - lastSampleMs >= SAMPLE_INTERVAL_MS) {
    lastSampleMs = now;
    float dt = readThermo(thermoDT);
    float ht = readThermo(thermoHT);

    if (isnan(dt) || isnan(ht)) {
      triggerFault(isnan(dt) ? "DT probe disconnected" : "HT probe disconnected");
    } else if (dt > HARD_CUTOFF_C || ht > HARD_CUTOFF_C) {
      triggerFault("hard cutoff exceeded (" + String(dt > ht ? dt : ht, 1) + "C)");
    }

    lastDT = dt; lastHT = ht;
    if (!isnan(dt)) updateRoR(now, dt);

    appendLogRow(lastDT, lastHT, lastRoR);

    JsonDocument doc;
    buildStateJson(doc);
    String out;
    serializeJson(doc, out);
    events.send(out.c_str(), "state", millis());
  }

  serviceSSR();
}
