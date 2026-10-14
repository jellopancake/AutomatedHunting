#include "ServoController.h"
#include "Config.h"
#include <EEPROM.h>

constexpr uint16_t EEPROM_MAGIC = 0xABCE;
constexpr int EEPROM_ADDRESS = 0;

// Default angles, in the same order as the Key enum.
const uint8_t DEFAULT_ANGLES[KEY_COUNT] = {
    60,   // LEFT
    60,   // RIGHT
    120,  // DOWN
    60,   // F
    120,  // G
    60,   // H
    120,  // J
    60,   // COLON
    120,  // APOS
    60,   // ALT
    120,  // CTRL
    60,   // SPACE
    120,  // SPACE2
    120,  // DEL
    60    // ENTER
};

AngleConfig angleConfig;

Servo Servo1, Servo2, Servo3, Servo4;
Servo Servo5, Servo6, Servo7, Servo8;

void initializeServos() {
    Servo1.attach(SERVO_ALT_SPACE_2_PIN);
    Servo2.attach(SERVO_F_G_PIN);
    Servo3.attach(SERVO_H_J_PIN);
    Servo4.attach(SERVO_ALT_SPACE_PIN);
    Servo5.attach(SERVO_COLON_APOSTROPHE_PIN);
    Servo6.attach(SERVO_CTRL_LEFT_PIN);
    Servo7.attach(SERVO_DOWN_RIGHT_PIN);
    Servo8.attach(SERVO_DEL_ENTER_PIN);

    resetServos();
}

void initializeKeyAngles() {
    EEPROM.get(EEPROM_ADDRESS, angleConfig);

    bool valid = angleConfig.magic == EEPROM_MAGIC;

    // Validate every stored angle.
    if (valid) {
        for (int i = 0; i < KEY_COUNT; i++) {
            if (angleConfig.angles[i] > 180) {
                valid = false;
                break;
            }
        }
    }

    // First run, invalid data, or corrupted configuration.
    if (!valid) {
        angleConfig.magic = EEPROM_MAGIC;

        for (int i = 0; i < KEY_COUNT; i++) {
            angleConfig.angles[i] = DEFAULT_ANGLES[i];
        }

        EEPROM.put(EEPROM_ADDRESS, angleConfig);
    }
}

void resetServos() {
    Servo* servos[] = {
        &Servo1, &Servo2, &Servo3, &Servo4,
        &Servo5, &Servo6, &Servo7
    };

    for (Servo* servo : servos) {
        servo->write(90);
        delay(200);
    }
}

// Basic button input control //////////////////////////////////////////////////////////////////////////////////////////////////
void pressButton(Key key) {
    int angle = keyToAngle(key);
    Servo* servo = keyToServo(key);

    if (servo == nullptr) {
        return;
    }

    servo->write(angle);
    delay(600);
    servo->write(90);
}


void shortPressButton(Key key) {
    int angle = keyToAngle(key);
    Servo* servo = keyToServo(key);

    if (servo == nullptr) return;

    servo->write(angle);
    delay(320);
    servo->write(90);
}

void holdButton(Key key, float holdTime) {
    int angle = keyToAngle(key);
    Servo* servo = keyToServo(key);

    if (servo == nullptr) return;

    servo->write(angle);
    delay(holdTime * 1000);
    servo->write(90);
}

void pressDownButton(Key key) {
    int angle = keyToAngle(key);
    Servo* servo = keyToServo(key);

    if (servo == nullptr) return;

    servo->write(angle);
}

void releaseButton(Key key) {
    Servo* servo = keyToServo(key);

    if (servo == nullptr) return;

    servo->write(90);
}

// Servo decision making /////////////////////////////////////////////////////////////////////////////////////////////

Servo* keyToServo(Key key) {
    if (key == SPACE) {
        return &Servo1;
    }
    else if (key == F || key == G) {
        return &Servo2;
    }
    else if (key == H || key == J) {
        return &Servo3;
    }
    else if (key == ALT || key == SPACE2) {
        return &Servo4;
    }
    else if (key == COLON || key == APOS) {
        return &Servo5;
    }
    else if (key == CTRL || key == LEFT) {
        return &Servo6;
    }
    else if (key == RIGHT || key == DOWN) {
        return &Servo7;
    }
    else if (key == DEL || key == ENTER) {
        return &Servo8;
    }

    Serial.println("No servo found");
    return nullptr;
}

int keyToAngle(Key key) {
    int index = static_cast<int>(key);

    if (index < 0 || index >= KEY_COUNT) {
        Serial.println("No keys match");
        return 90;
    }

    return angleConfig.angles[index];
}

// Editing Servo angle values /////////////////////////////////////////////////////////////////////////////////////////
bool setKeyAngle(Key key, int angle) {
    int index = static_cast<int>(key);

    if (index < 0 || index >= KEY_COUNT ||
        angle < 0 || angle > 180) {
        return false;
    }

    if (angleConfig.angles[index] == angle) {
        return true;  // Nothing changed; no EEPROM write needed.
    }

    angleConfig.angles[index] = angle;

    EEPROM.put(EEPROM_ADDRESS, angleConfig);

    // Test the angle
    Servo* servo = keyToServo(key);
    servo->write(angle);

    delay(500);

    servo->write(90);

    return true;
}
