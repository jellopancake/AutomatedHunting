#ifndef COMMANDS_H
#define COMMANDS_H

#include "Config.h"

void swapChars();

void upTeleport();
void downTeleport();

void walk(Key dir, int time);

void startJumpGlide(int param);
void endJumpGlide(int param);

void walkShortDistance(int param);
void fastTeleport(int param);

void startHoldAttack(int param);
void endHoldAttack(int param);

Key selectDir(int param);
Key selectSkill(int param);

void useSkill(int param);
void jumpSkill(int param);
void delayedJumpSkill(int param);

void doubleJumpAttack();
void shortDoubleJumpAttack();
void doubleJump();

void startWalk(int param);
void endWalk(int param);

void upJump();
void shortUpJump();
void upJumpWarrior();
void downJump();

#endif