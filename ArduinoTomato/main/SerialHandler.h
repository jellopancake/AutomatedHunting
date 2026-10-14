#ifndef SERIAL_HANDLER_H
#define SERIAL_HANDLER_H

#include <Arduino.h>

extern uint8_t serialBuffer[3];

void initializeSerial();
void readSerialToBuffer();
void clearSerialBuffer();
void reestablishSerialConnection();

#endif