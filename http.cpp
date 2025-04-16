#include <WiFi.h> // Or <ESP8266WiFi.h>
#include <HTTPClient.h> // Or <ESP8266HTTPClient.h>
#include <ArduinoJson.h> // For creating JSON body
#include <SPI.h>
#include <MFRC522.h> // Assuming MFRC522 RFID reader

#define SS_PIN  5  // SDA Pin
#define RST_PIN 22 // RST Pin
MFRC522 rfid(SS_PIN, RST_PIN);

const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";
const char* serverUrl = "http://<YOUR_FASTAPI_SERVER_IP>:8000/api/scan"; // CHANGE THIS

void setup() {
  Serial.begin(115200);
  SPI.begin(); // Init SPI bus
  rfid.PCD_Init(); // Init MFRC522

  // Connect to Wi-Fi
  Serial.print("Connecting to ");
  Serial.println(ssid);
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi connected.");
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());
}

void loop() {
  // Try to detect new RFID card
  if (rfid.PICC_IsNewCardPresent() && rfid.PICC_ReadCardSerial()) {
    String tagUID = "";
    for (byte i = 0; i < rfid.uid.size; i++) {
      tagUID += String(rfid.uid.uidByte[i] < 0x10 ? "0" : "");
      tagUID += String(rfid.uid.uidByte[i], HEX);
    }
    tagUID.toUpperCase();
    Serial.println("Scanned RFID: " + tagUID);

    // Send the tag to the backend
    sendRFIDToServer(tagUID);

    rfid.PICC_HaltA(); // Halt PICC
    rfid.PCD_StopCrypto1(); // Stop encryption on PCD

    delay(2000); // Wait a bit after sending before scanning again
  }
  delay(50);
}

void sendRFIDToServer(String rfidTag) {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    WiFiClient client; // Needed for HTTPClient on ESP8266? Check library docs.

    Serial.print("[HTTP] begin...\n");
    if (http.begin(client, serverUrl)) { // Use client instance if needed by library
      http.addHeader("Content-Type", "application/json");

      // Create JSON body
      StaticJsonDocument jsonDoc; // Adjust size as needed
      jsonDoc["rfid"] = rfidTag;
      String requestBody;
      serializeJson(jsonDoc, requestBody);

      Serial.print("[HTTP] POSTING: ");
      Serial.println(requestBody);

      int httpCode = http.POST(requestBody);

      if (httpCode > 0) {
        Serial.printf("[HTTP] POST... code: %d\n", httpCode);
        if (httpCode == HTTP_CODE_OK || httpCode == HTTP_CODE_CREATED) {
           String payload = http.getString();
           Serial.println("Received payload:\n<<");
           Serial.println(payload);
           Serial.println(">>");
           // TODO: Add success indication (e.g., green LED)
        } else if (httpCode == 429) {
           Serial.println("Server indicated cooldown is active.");
           // TODO: Add feedback for cooldown (e.g., yellow LED)
        } else {
           Serial.printf("POST failed, error: %s\n", http.errorToString(httpCode).c_str());
           // TODO: Add error indication (e.g., red LED)
        }
      } else {
        Serial.printf("[HTTP] POST... failed, error: %s\n", http.errorToString(httpCode).c_str());
        // TODO: Add error indication (e.g., red LED)
      }
      http.end();
    } else {
      Serial.printf("[HTTP] Unable to connect\n");
    }
  } else {
    Serial.println("WiFi Disconnected");
  }
}