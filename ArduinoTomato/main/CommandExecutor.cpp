#include "CommandExecutor.h"
#include "Commands.h"
#include "Config.h"
#include "SerialHandler.h"
#include "Servocontroller.h"

void executeCommand() {
    if (serialBuffer[2] == 255) {
        return;
    }

    char prefix = serialBuffer[0];
    char command = serialBuffer[1];
    int param = serialBuffer[2] - '0';

    // Configuration command
    if (prefix == '*') {
        doubleJumpDelay = (serialBuffer[1] - '0') * 20;
        shortDoubleJumpDelay = 60 + (serialBuffer[2] - '0') * 20;

        clearSerialBuffer();
        return;
    }
    // Calibration command
    else if (prefix == '<' || prefix == '>') {
      calcAndSetNewKeyAngle(prefix, serialBuffer[1], serialBuffer[2]);
    }
    // Regular command
    else if (prefix == '+') {
      switch (command) {
        case 'A': startWalk(param); break;
        case 'B': endWalk(param); break;
        case 'C': doubleJump(); break;
        case 'D': doubleJumpAttack(); break;
        case 'E': shortDoubleJumpAttack(); break;
        case 'F': upJump(); break;
        case 'G': upJumpWarrior(); break;
        case 'H': downJump(); break;
        case 'I': useSkill(param); break;
        case 'J': jumpSkill(param); break;

        case 'L': startHoldAttack(param); break;
        case 'M': endHoldAttack(param); break;
        case 'N': resetServos(); break;
        case 'O': fastTeleport(param); break;

        case 'Q': walkShortDistance(param); break;
        case 'R': shortUpJump(); break;
        case 'S': startJumpGlide(param); break;
        case 'T': endJumpGlide(param); break;
        case 'U': upTeleport(); break;
        case 'V': downTeleport(); break;
        case 'X': delayedJumpSkill(param); break;

        default:
            // Unknown or currently unused command.
            break;
      }
    }

    clearSerialBuffer();
}

void calcAndSetNewKeyAngle(char param1, char param2, char param3){
  // Find which key to adjust
  int keyNum = param2 - '0';
  if (param1 == '<') {
    // Do nothing
  }
  else if (param1 == '>'){
    keyNum += 10;
  }

  // Calculate delta angle to adjust by
  int deltaAngle = param3 - '0';
  // Map 5 -> 9 to +1 -> +5
  if (deltaAngle >= 5){
    deltaAngle -= 4;
  }
  // Map 0 -> 4 to -5 -> -1
  else {
    deltaAngle -= 5;
  }

  if (keyNum >= 0 && keyNum < KEY_COUNT){
    Key key = static_cast<Key>(keyNum);
    int currentAngle = angleConfig.angles[keyNum];
    int newAngle;

    // Adjust the direction of the change depending on which side of the servo the key is on
    if (currentAngle >= 90) {
        newAngle = currentAngle + deltaAngle;
    }
    else {
        newAngle = currentAngle - deltaAngle;
    }

    newAngle = constrain(newAngle, 0, 180);
    setKeyAngle(key, newAngle);

  }
}