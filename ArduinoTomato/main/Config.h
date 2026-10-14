#ifndef CONFIG_H
#define CONFIG_H

#include <Arduino.h>

// Servo pins
constexpr uint8_t SERVO_ALT_SPACE_2_PIN = 3;
constexpr uint8_t SERVO_F_G_PIN = 4;
constexpr uint8_t SERVO_H_J_PIN = 5;
constexpr uint8_t SERVO_ALT_SPACE_PIN = 6;
constexpr uint8_t SERVO_COLON_APOSTROPHE_PIN = 7;
constexpr uint8_t SERVO_CTRL_LEFT_PIN = 8;
constexpr uint8_t SERVO_DOWN_RIGHT_PIN = 9;
constexpr uint8_t SERVO_DEL_ENTER_PIN = 11;

// Timing defaults
constexpr int DEFAULT_DOUBLE_JUMP_DELAY = 80;
constexpr int DEFAULT_SHORT_DOUBLE_JUMP_DELAY = 180;

// Key identifiers
enum Key {
    LEFT, RIGHT, DOWN, F, G, H, J,
    COLON, APOS, ALT, CTRL, SPACE, SPACE2,
    DEL, ENTER, INVALID
};

// Key aliases
extern Key left;
extern Key right;
extern Key down;
extern Key up;
extern Key jump;
extern Key altJump;
extern Key skill1;
extern Key skill2;
extern Key skill3;
extern Key skill4;
extern Key skill5;
extern Key mainAttack;
extern Key skill0;
extern Key escape;
extern Key enter;

// Runtime-adjustable settings
extern int doubleJumpDelay;
extern int shortDoubleJumpDelay;

#endif