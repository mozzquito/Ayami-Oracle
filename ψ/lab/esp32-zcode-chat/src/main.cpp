#include <Arduino.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include "secrets.h"

void connectWiFi() {
  Serial.printf("Connecting to WiFi: %s\n", WIFI_SSID);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  while (WiFi.status() != WL_CONNECTED) {
    delay(300);
    Serial.print(".");
  }
  Serial.printf("\nWiFi connected, IP: %s\n", WiFi.localIP().toString().c_str());
}

String askZcode(const String &prompt) {
  HTTPClient http;
  http.setTimeout(60000); // zcode can take a while to think
  String url = String("http://") + BRIDGE_HOST + ":" + String(BRIDGE_PORT) + "/ask";
  if (!http.begin(url)) {
    return "[error] could not begin http connection to bridge";
  }
  http.addHeader("content-type", "application/json");

  JsonDocument reqDoc;
  reqDoc["prompt"] = prompt;
  String body;
  serializeJson(reqDoc, body);

  int status = http.POST(body);
  String result;
  if (status == 200) {
    JsonDocument resDoc;
    DeserializationError err = deserializeJson(resDoc, http.getString());
    if (err) {
      result = "[error] json parse failed: " + String(err.c_str());
    } else {
      result = resDoc["answer"].as<String>();
    }
  } else {
    result = "[error] bridge http status " + String(status) + ": " + http.getString();
  }
  http.end();
  return result;
}

String inputBuffer;

void setup() {
  Serial.begin(115200);
  delay(1000);
  connectWiFi();
  Serial.println("Ready. Type a prompt and press Enter:");
}

void loop() {
  while (Serial.available()) {
    char c = Serial.read();
    if (c == '\n') {
      inputBuffer.trim();
      if (inputBuffer.length() > 0) {
        Serial.println("Thinking...");
        String answer = askZcode(inputBuffer);
        Serial.println("zcode: " + answer);
        Serial.println();
        Serial.println("Type a prompt and press Enter:");
      }
      inputBuffer = "";
    } else if (c != '\r') {
      inputBuffer += c;
    }
  }
}
