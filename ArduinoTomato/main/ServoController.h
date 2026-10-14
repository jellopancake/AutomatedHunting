
#ifndef SERVO_CONTROLLER_H
#define SERVO_CONTROLLER_H

#include <Arduino.h>
#include <Servo.h>
#include <stdint.h>
#include "Config.h"

constexpr uint8_t KEY_COUNT = INVALID;

// Servo angle configuration stored in EEPROM.
struct AngleConfig {
    uint16_t magic;
    uint8_t angles[KEY_COUNT];
};

// Shared angle configuration.
extern AngleConfig angleConfig;

// Servo objects.
extern Servo Servo1, Servo2, Servo3, Servo4;
extern Servo Servo5, Servo6, Servo7, Servo8;

// Initialization.
void initializeServos();
void initializeKeyAngles();

// Servo control.
void resetServos();
void pressButton(Key key);
void shortPressButton(Key key);
void holdButton(Key key, float holdTime);
void pressDownButton(Key key);
void releaseButton(Key key);

// Key-to-servo and key-to-angle mapping.
Servo* keyToServo(Key key);
int keyToAngle(Key key);

// Angle calibration.
bool setKeyAngle(Key key, int angle);

#endif
