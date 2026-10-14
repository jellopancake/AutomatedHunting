#include "Config.h"
#include "ServoController.h"
#include "SerialHandler.h"
#include "CommandExecutor.h"

void setup() {
    initializeKeyAngles();
    initializeServos();
    initializeSerial();
}

void loop() {
    if (Serial) {
        readSerialToBuffer();
    } else {
        reestablishSerialConnection();
    }

    executeCommand();
}