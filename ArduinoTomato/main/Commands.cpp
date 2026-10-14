#include "Commands.h"
#include "ServoController.h"

// Paste the existing movement and skill function
// implementations here, unchanged initially.

// Preset inputs //////////////////////////////////////////////////////////////////////////////////////////////////
/*void swapChars(){
   pressButton(escape);
   delay(3000);
   pressButton(escape);
   delay(3000);
   pressButton(enter);
   delay(3000);
   pressButton(enter);
   delay(3000);
   pressButton(enter);
   delay(3000);
   pressButton(escape);
   delay(3000);
   pressButton(escape);
   delay(3000);
   pressButton(right);
   delay(3000);
   pressButton(enter);
   delay(3000);
   pressButton(right);
   delay(3000);
   pressButton(enter);
   delay(3000);
   pressButton(enter);
}*/

// For mages with teleport
void upTeleport(){
   pressDownButton(up);
   delay(500);
   pressButton(skill2);
   delay(200);
   releaseButton(up);
   delay(100);
}

void downTeleport(){
   pressDownButton(down);
   delay(600);
   shortPressButton(skill2);
   delay(200);
   releaseButton(down);
   delay(100);
}

// For demon classes, lets you jump into starting gliding in one direction
void startJumpGlide(int param){
   Key dir = selectDir(param);
   if (dir == INVALID) return;

   pressDownButton(dir);
   delay(200);
   shortPressButton(altJump);
   delay(doubleJumpDelay);
   pressDownButton(jump);
}

void endJumpGlide(int param){
   Key dir = selectDir(param);
   if (dir == INVALID) return;
   releaseButton(dir);
   releaseButton(jump);
}

void walkShortDistance(int param){
   Key dir = selectDir(param);
   if (dir == INVALID) return;

   walk(dir, 240);
   delay(200);
}

// Walks a short amount in one direction then does a double jump to the opposite direction
void fastTeleport(int param){
   Key dir = selectDir(param);
   if (dir == INVALID) return;

   pressDownButton(dir);
   delay(750);
   pressButton(skill2);
   delay(150);
   releaseButton(dir);
   delay(500);
   pressButton(mainAttack);
   delay(500);
}

void walk(Key dir, int time){
   pressDownButton(dir);
   delay(time);
   releaseButton(dir);
   delay(200);
}

void startHoldAttack(int param){
   Key skill = selectSkill(param);
   if (skill == INVALID) return;

   pressDownButton(skill);
}

void endHoldAttack(int param){
   Key skill = selectSkill(param);
   if (skill == INVALID) return;

   releaseButton(skill);
}

// Uses a skill, main attack, or fountain
void useSkill(int param){
   Key skill = selectSkill(param);
   if (skill == INVALID) return;

   if (skill == skill0){
      delay(500);
      shortPressButton(skill);
      delay(500);
   }
   else {
      delay(500);
      pressButton(skill);
      delay(500);
   }
}

// Jumps and uses a skill or main attack
void jumpSkill(int param){
   Key skill = selectSkill(param);
   if (skill == INVALID) return;

   delay(300);
   shortPressButton(altJump);
   pressButton(skill);
}

void delayedJumpSkill(int param){
   Key skill = selectSkill(param);
   if (skill == INVALID) return;

   delay(300);
   shortPressButton(altJump);
   delay(180);
   pressButton(skill);
}

Key selectSkill(int param) {
    switch (param) {
        case 0: return skill0;
        case 1: return skill1;
        case 2: return skill2;
        case 3: return skill3;
        case 4: return skill4;
        case 5: return mainAttack;
        case 6: return up;
        case 7: return down;
        case 8: return skill5;
        default: return INVALID;
    }
}

// Performs a flashjump with an attack
void doubleJumpAttack(){
   delay(100);
   shortPressButton(altJump);
   delay(doubleJumpDelay);
   pressDownButton(jump);
   delay(100);
   shortPressButton(mainAttack);
   releaseButton(jump);
   delay(100);
}

// Performs a shorter flashjump with an attack
void shortDoubleJumpAttack(){
   delay(200);
   shortPressButton(altJump);
   delay(shortDoubleJumpDelay);
   pressDownButton(jump);
   delay(100);
   pressDownButton(mainAttack);
   delay(350);
   releaseButton(mainAttack);
   releaseButton(jump);
   delay(250);
}

// Performs a flashjump
void doubleJump(){
   pressButton(altJump);
   delay(doubleJumpDelay);
   pressButton(jump);
   delay(200);   
}

// Starts walking in a given direction
void startWalk(int param){
   Key dir = selectDir(param);
   if (dir == INVALID) return;

   pressDownButton(dir);
}

// Stops walking in a given direction
void endWalk(int param){
   Key dir = selectDir(param);
   if (dir == INVALID) return;

   releaseButton(dir);
}

Key selectDir(int param){
   Key dir;
   if (param == 0){
      dir = left;
   }
   else if(param == 1){
      dir = right;
   } 
   else {
      dir = INVALID;
   }
   return dir;
}

// Performs an upjump by holding up and inputting two jumps quickly
void upJump(){
   pressDownButton(up);
   delay(150);
   shortPressButton(altJump);
   delay(doubleJumpDelay);
   shortPressButton(jump);
   releaseButton(up);
   delay(100); 
}

// Performs an upjump by holding up and inputting two jumps quickly
void shortUpJump(){
   pressDownButton(up);
   delay(150);
   shortPressButton(altJump);
   delay(shortDoubleJumpDelay);
   pressButton(jump);
   releaseButton(up);
   pressButton(mainAttack);
   delay(100); 
}

// Performs an upjump by pressing the upward charge skill for warrior classes
void upJumpWarrior(){
   pressButton(skill2);
}

// Performs a downjump to bring the character one platform below it
void downJump(){
   pressDownButton(down);
   delay(400);
   shortPressButton(jump);
   delay(200);
   releaseButton(down);
   delay(100);
}

