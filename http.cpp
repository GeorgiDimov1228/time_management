#include <WiFi.h>        // For ESP32 WiFi
#include <HTTPClient.h>  // For ESP32 HTTP requests
#include <ArduinoJson.h> // For creating JSON body
#include <SPI.h>
#include <MFRC522.h>     // For RFID reader

#define SS_PIN  5  // Your MFRC522's SDA/SS/CS pin connected to ESP32 GPIO5
#define RST_PIN 22 // Your MFRC522's RST pin connected to ESP32 GPIO22

// LED pin definitions (optional, but helpful for visual feedback)
#define GREEN_LED_PIN 12  // Success indication
#define YELLOW_LED_PIN 14 // Cooldown indication
#define RED_LED_PIN 27    // Error indication

MFRC522 rfid(SS_PIN, RST_PIN); // Create MFRC522 instance

// Network credentials
const char* ssid = "USERNAME";                 
const char* password = "PASSS";         
const char* serverUrl = "http://IPOFSERVER/api/scan";

void setup() {
  Serial.begin(115200); // Initialize serial communication
  SPI.begin();          // Init SPI bus
  rfid.PCD_Init();      // Init MFRC522
  rfid.PCD_DumpVersionToSerial(); // Optional: prints MFRC522 version to Serial Monitor
  Serial.println("RFID Reader Initialized.");

  // Setup LED pins
  pinMode(GREEN_LED_PIN, OUTPUT);
  pinMode(YELLOW_LED_PIN, OUTPUT);
  pinMode(RED_LED_PIN, OUTPUT);
  
  // Turn all LEDs off initially
  digitalWrite(GREEN_LED_PIN, LOW);
  digitalWrite(YELLOW_LED_PIN, LOW);
  digitalWrite(RED_LED_PIN, LOW);

  // Connect to Wi-Fi
  Serial.print("Connecting to ");
  Serial.println(ssid);
  WiFi.begin(ssid, password);
  int wifi_retries = 0;
  while (WiFi.status() != WL_CONNECTED && wifi_retries < 30) { // Try for about 15 seconds
    delay(500);
    Serial.print(".");
    wifi_retries++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\nWiFi connected.");
    Serial.print("IP address: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("\nFailed to connect to WiFi. Please check credentials or network.");
    // Optionally blink red LED or take other action if WiFi fails
    while(true) { // Halt if WiFi connection fails
        digitalWrite(RED_LED_PIN, !digitalRead(RED_LED_PIN)); // Blink red LED
        delay(500);
    }
  }
}

void loop() {
  // If not connected to WiFi, don't proceed (already handled in setup for initial, but good check)
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi disconnected. Attempting to reconnect...");
    WiFi.begin(ssid, password); // Attempt to reconnect
    int wifi_retries = 0;
    while (WiFi.status() != WL_CONNECTED && wifi_retries < 20) { // Try for 10 seconds
        delay(500);
        Serial.print(".");
        wifi_retries++;
    }
    if (WiFi.status() != WL_CONNECTED) {
        Serial.println("Reconnect failed. Will retry later.");
        delay(5000); // Wait before trying loop again
        return; // Skip the rest of the loop if still not connected
    }
    Serial.println("\nWiFi reconnected.");
    Serial.print("IP address: ");
    Serial.println(WiFi.localIP());
  }

  // Try to detect new RFID card
  if (rfid.PICC_IsNewCardPresent() && rfid.PICC_ReadCardSerial()) {
    String tagUID = "";
    for (byte i = 0; i < rfid.uid.size; i++) {
      tagUID += String(rfid.uid.uidByte[i] < 0x10 ? "0" : ""); // Add leading zero if needed
      tagUID += String(rfid.uid.uidByte[i], HEX);
    }
    tagUID.toUpperCase(); // Convert to uppercase for consistency
    Serial.println("Scanned RFID: " + tagUID);

    // Send the tag to the backend
    sendRFIDToServer(tagUID);

    rfid.PICC_HaltA();      // Halt PICC
    rfid.PCD_StopCrypto1(); // Stop encryption on PCD (if used, good practice)

    delay(2000); // Wait a bit after sending before allowing another scan
  }
  delay(50); // Short delay in the main loop
}

// Helper function to reset all LEDs
void resetLEDs() {
  digitalWrite(GREEN_LED_PIN, LOW);
  digitalWrite(YELLOW_LED_PIN, LOW);
  digitalWrite(RED_LED_PIN, LOW);
}

void sendRFIDToServer(String rfidTag) {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http; // Create HTTPClient object

    Serial.print("[HTTP] begin to: ");
    Serial.println(serverUrl);

    // For ESP32, http.begin(serverUrl) is often sufficient
    if (http.begin(serverUrl)) { 
      http.addHeader("Content-Type", "application/json");

      // Create JSON body
      StaticJsonDocument<256> jsonDoc; // Specify a size, e.g., 256 bytes

                                      // 64 might be okay, 128 is safer.
      jsonDoc["rfid"] = rfidTag;
      String requestBody;
      serializeJson(jsonDoc, requestBody);

      Serial.print("[HTTP] POSTING: ");
      Serial.println(requestBody);

      int httpCode = http.POST(requestBody);

      if (httpCode > 0) {
        Serial.printf("[HTTP] POST... code: %d\n", httpCode);
        String payload = http.getString(); // Get response payload AFTER checking httpCode > 0

        if (httpCode == HTTP_CODE_OK || httpCode == HTTP_CODE_CREATED) {
           Serial.println("Received payload:\n<<");
           Serial.println(payload);
           Serial.println(">>");
           resetLEDs();
           digitalWrite(GREEN_LED_PIN, HIGH); // Turn on green LED for success
           Serial.println("Success");
           delay(2000); // Show LED for 2 seconds
           digitalWrite(GREEN_LED_PIN, LOW); 

        } else if (httpCode == 401) { // Specifically handle 401
           Serial.println("Server returned 401 Unauthorized. Check authentication on API or ESP32.");
           Serial.println("Payload (if any):\n<<");
           Serial.println(payload);
           Serial.println(">>");
           resetLEDs();
           digitalWrite(RED_LED_PIN, HIGH); 
           Serial.println("Error - Unauthorized");
           delay(2000); 
           digitalWrite(RED_LED_PIN, LOW);

        } else if (httpCode == 429) {
           Serial.println("Server indicated cooldown is active.");
           Serial.println("Payload (if any):\n<<");
           Serial.println(payload);
           Serial.println(">>");
           resetLEDs();
           digitalWrite(YELLOW_LED_PIN, HIGH); 
           Serial.println("Cooldown");
           delay(2000); 
           digitalWrite(YELLOW_LED_PIN, LOW); 
           
        } else {
           Serial.printf("POST failed, other error. Payload (if any):\n<<\n");
           Serial.println(payload);
           Serial.println(">>");
           resetLEDs();
           digitalWrite(RED_LED_PIN, HIGH); 
           Serial.printf("Error - HTTP %d\n", httpCode);
           delay(2000); 
           digitalWrite(RED_LED_PIN, LOW); 
        }
      } else {
        Serial.printf("[HTTP] POST... failed, error: %s\n", http.errorToString(httpCode).c_str());
        resetLEDs();
        digitalWrite(RED_LED_PIN, HIGH); 
        Serial.println("Error - POST failed (e.g., connection refused, DNS issue)");
        delay(2000); 
        digitalWrite(RED_LED_PIN, LOW); 
      }
      http.end(); // Free resources
      delay(50);  // Small delay to allow LwIP to clean up if needed
    } else {
      Serial.printf("[HTTP] Unable to connect / http.begin() failed for: %s\n", serverUrl);
      resetLEDs();
      digitalWrite(RED_LED_PIN, HIGH); 
      Serial.println("Error - HTTP begin failed");
      delay(2000); 
      digitalWrite(RED_LED_PIN, LOW); 
    }
  } else {
    Serial.println("WiFi Disconnected before sending HTTP request.");
    resetLEDs();
    digitalWrite(RED_LED_PIN, HIGH); // Turn on red LED for error
    delay(2000); 
    digitalWrite(RED_LED_PIN, LOW); 
  }
}