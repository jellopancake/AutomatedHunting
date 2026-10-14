#include "SerialHandler.h"
#include "Config.h"

uint8_t serialBuffer[3] = {255, 255, 255};

static bool handshakeDone = false;

void initializeSerial() {
    Serial.begin(9600);
    Serial.setTimeout(1);
    clearSerialBuffer();
}

// Reads serial data to the buffer
void readSerialToBuffer(){
   // Handshake to check if arduino is available
   if (!handshakeDone && Serial.available()) {
      String input = Serial.readStringUntil('\n');
      input.trim();  // Remove whitespace/newlines

      if (input == "SYN") {
         Serial.println("SYN-ACK");
      } else if (input == "ACK") {
         Serial.println("READY");
         handshakeDone = true;
    }
   }
   
   if (handshakeDone) {
      if (Serial.available() >= 3){   
         for(int i = 0; i < sizeof(serialBuffer); i++){        
            serialBuffer[i] = Serial.read();
         }
         handshakeDone = false;
      }
   }
}

void clearSerialBuffer() {
    memset(serialBuffer, 255, sizeof(serialBuffer));
}

// Resets serial connections
void reestablishSerialConnection(){
   Serial.end();
   delay(1000);
   Serial.begin(9600);
}