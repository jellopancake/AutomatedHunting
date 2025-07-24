// Include the Servo library 
#include <Servo.h>

// Declare the Servo pin 
int servo_alt_space_2 = 3;
int servo_F_G = 4;
int servo_H_J = 5;
int servo_alt_space = 6;
int servo_colon_apostrophe = 7;
int servo_ctrl_left = 8;
int servo_down_right = 9;

// Preset values based on class
int doubleJumpDelay = 250;
int shortDoubleJumpDelay = 350;

// Serial buffer for collecting incoming serial data
// Use 255 as null case
uint8_t serialBuffer[] = {255, 255, 255};

enum Key{LEFT, RIGHT, DOWN, F, G, H, J, COLON, APOS, ALT, CTRL, SPACE, SPACE2};
   Key left = LEFT;
   Key right = RIGHT;
   Key down = DOWN;
   Key up = COLON;
   Key jump = SPACE;
   Key altJump = SPACE2;
   Key skill1 = CTRL;
   Key skill2 = H;
   Key skill3 = J;
   Key skill4 = ALT;
   Key swap = APOS;
   Key mainAttack = F;
   Key skill0 = G; // Ropelift

// Create a servo object 
Servo Servo1, Servo2, Servo3, Servo4, Servo5, Servo6, Servo7;
void setup() { 
   // We need to attach the servo to pins 3-9
   Servo1.attach(servo_alt_space_2); 
   Servo2.attach(servo_F_G); 
   Servo3.attach(servo_H_J); 
   Servo4.attach(servo_alt_space); 
   Servo5.attach(servo_colon_apostrophe);
   Servo6.attach(servo_ctrl_left); 
   Servo7.attach(servo_down_right); 
   
   // Initialize in horizontal position
   Servo1.write(90);
   Servo2.write(90);
   Servo3.write(90);
   Servo4.write(90);
   Servo5.write(90);
   Servo6.write(90);
   Servo7.write(90);

   // Start open Serial port through USB
   Serial.begin(9600);  
   Serial.setTimeout(1);

   // Clear any leftover memory variables from previous runtimes
   clearSerialBuffer();
}

void loop(){
   // This is the main serial loop receiving commands from the PC
   if (Serial) {  // Check if serial is still available
      readSerialToBuffer();
   } else {
      reestablishSerialConnection();
   }   

   // If serial communication sends a command, this tries to execute the command
   executeCommand();
}

// Resets serial connections
void reestablishSerialConnection(){
   Serial.end();
   delay(1000);
   Serial.begin(9600);
}

// Chooses the command to execute based off the instructions received through serial communication
void executeCommand(){
   // Once we have a full command in our serial buffer, start executing the command
   if(serialBuffer[2] != 255){
      // Running setup
      if(serialBuffer[0] == '*'){
         int delay1 = serialBuffer[1] - '0';
         doubleJumpDelay = 200 + delay1*20;

         int delay2 = serialBuffer[2] - '0';
         shortDoubleJumpDelay = 300 + delay2*20;
      }

      // Running commands
      if (serialBuffer[0] == '+'){
         int command = serialBuffer[1];
         int param = serialBuffer[2] - '0';

         if (command == 'A'){
            startWalk(param);

         }
         else if (command == 'B'){
            endWalk(param);

         }
         else if (command == 'C'){
            doubleJump();

         }
         else if (command == 'D'){
            doubleJumpAttack();

         }
         else if (command == 'E'){
            shortDoubleJumpAttack();

         }
         else if (command == 'F'){
            upJump();

         }
         else if (command == 'G'){
            upJumpWarrior();

         }
         else if (command == 'H'){
            downJump();

         }
         else if (command == 'I'){            
            useSkill(param);

         }
         else if (command == 'J'){
            jumpSkill(param);

         }
         else if (command == 'K'){
            swapKeyboardLayout();

         }
         else if (command == 'L'){
            startHoldAttack(param);

         }
         else if(command == 'M'){
            endHoldAttack(param);

         }
         else if(command == 'N'){
            // Reset to horizontal position
            Servo1.write(90);
            Servo2.write(90);
            Servo3.write(90);
            Servo4.write(90);
            Servo5.write(90);
            Servo6.write(90);
            Servo7.write(90);
         }
         else if(command == 'O'){
            walkOppositeIntoDoubleJump(param);
         }
         else if (command == 'P'){
            walkOppositeIntoShortDoubleJump(param);
         }
         else if(command == 'Q'){
            walkShortDistance(param);
         }
         else if(command == 'R'){
            shortUpJump();
         }
         else if(command == 'S'){
            startJumpGlide(param);
         }
         else if(command == 'T'){
            endJumpGlide(param);
         }
      }
      // Clear the buffer for the next command
      clearSerialBuffer();
   }
}

// Reads serial data to the buffer
void readSerialToBuffer(){
   if (Serial.available() >= 3){   
      // Only start reading message if it starts with ack
      if(Serial.peek() == '+' || Serial.peek() == '*'){
         // Overwrite empty spaces in the serial buffer with the received serial data
         for(int i = 0; i < sizeof(serialBuffer); i++){        
            // Removes end line characters
            if (Serial.peek() == '\n' || Serial.peek() == '\0'){
               Serial.read();
               break;
            }

            // Load message into serial buffer
            serialBuffer[i] = Serial.read();
         }
      }
      // If message does not start with ack, remove the byte from the buffer
      Serial.read();

   }
}


// Clears the serial buffer
void clearSerialBuffer(){
   memset(serialBuffer, 255, sizeof(serialBuffer));
}

// Preset inputs //////////////////////////////////////////////////////////////////////////////////////////////////

// For demon classes, lets you jump into starting gliding in one direction
void startJumpGlide(int param){
   Key dir = selectDir(param);
   pressDownButton(dir);
   delay(100);
   pressButton(altJump);
   delay(doubleJumpDelay);
   pressDownButton(jump);
}

void endJumpGlide(int param){
   Key dir = selectDir(param);
   releaseButton(dir);
   releaseButton(jump);
}

void walkShortDistance(int param){
   Key dir = selectDir(param);
   walk(dir, 200);
}

// Walks a short amount in one direction then does a double jump to the opposite direction
void walkOppositeIntoDoubleJump(int param){
   Key oppositeDir = selectOppositeDir(param);
   Key dir = selectDir(param);

   walk(oppositeDir, 350);
   delay(200);
   pressDownButton(dir);
   delay(150);
   doubleJumpAttack();
   releaseButton(dir);
}

// Walks a short amount in one direction then does a short double jump to the opposite direction
void walkOppositeIntoShortDoubleJump(int param){
   Key oppositeDir = selectOppositeDir(param);
   Key dir = selectDir(param);

   walk(oppositeDir, 350);
   delay(200);
   pressDownButton(dir);
   delay(150);
   shortDoubleJumpAttack();
   releaseButton(dir);
}

void walk(Key dir, int time){
   pressDownButton(dir);
   delay(time);
   releaseButton(dir);
}

void startHoldAttack(int param){
   Key skill = selectSkill(param);
   pressDownButton(skill);
}

void endHoldAttack(int param){
   Key skill = selectSkill(param);
   releaseButton(skill);
}

void swapKeyboardLayout(){
   delay(500);
   pressButton(swap);
   delay(500);
}

// Uses a skill, main attack, or fountain
void useSkill(int param){
   Key skill = selectSkill(param);

   delay(500);
   pressButton(skill);
   delay(500);
}

// Jumps and uses a skill or main attack
void jumpSkill(int param){
   Key skill = selectSkill(param);

   delay(200);
   pressButton(altJump);
   pressButton(skill);
}

Key selectSkill(int param){
   Key skill;
   if (param == 0){
      skill = skill0;
   }
   else if(param == 1){
      skill = skill1;
   }
   else if(param == 2){
      skill = skill2;
   }
   else if(param == 3){
      skill = skill3;
   }
   else if(param == 4){
      skill = skill4;
   }
   else if(param == 5){
      skill = mainAttack;
   }
   return skill;
}

// Performs a flashjump with an attack
void doubleJumpAttack(){
   delay(100);
   pressButton(altJump);
   delay(doubleJumpDelay);
   pressDownButton(jump);
   delay(100);
   pressButton(mainAttack);
   releaseButton(jump);
   delay(100);
}

// Performs a shorter flashjump with an attack
void shortDoubleJumpAttack(){
   delay(200);
   pressButton(altJump);
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
   pressDownButton(dir);
}

// Stops walking in a given direction
void endWalk(int param){
   Key dir = selectDir(param);
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
   return dir;
}

Key selectOppositeDir(int param){
   Key dir;
   if (param == 0){
      dir = right;
   }
   else if(param == 1){
      dir = left;
   }
   return dir;
}

// Performs an upjump by holding up and inputting two jumps quickly
void upJump(){
   pressDownButton(up);
   delay(200);
   pressButton(altJump);
   delay(160);
   pressButton(jump);
   releaseButton(up);
   delay(100); 
}

// Performs an upjump by holding up and inputting two jumps quickly
void shortUpJump(){
   pressDownButton(up);
   delay(200);
   pressButton(altJump);
   delay(250);
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
   delay(500);
   pressButton(jump);
   delay(200);
   releaseButton(down);
   delay(100);
}

// Basic button input control //////////////////////////////////////////////////////////////////////////////////////////////////
void pressButton(Key key){
   int angle = keyToAngle(key);
   Servo servo = keyToServo(key);
   
   servo.write(angle);
   delay(200);
   servo.write(90);
}

void holdButton(Key key, float holdTime){
   int angle = keyToAngle(key);
   Servo servo = keyToServo(key);

   servo.write(angle);
   delay(holdTime*1000);
   servo.write(90);
}

void pressDownButton(Key key){
   int angle = keyToAngle(key);
   Servo servo = keyToServo(key);
   
   servo.write(angle);

}

void releaseButton(Key key){
   Servo servo = keyToServo(key);
   
   servo.write(90);
}

// Start/Stop functionality ///////////////////////////////////////////////////////////////////////
// Servo Legend for angles required to press keyboard keys //////////////////////////////////////////////////////////////////////////////////////////////////
// LOW 10-70, HIGH 100-170
// Servo 1
// Angle LOW press space
// Angle HIGH press alt
// Servo 2
// Angle LOW press F
// Angle HIGH press G
// Servo 3
// Angle LOW press H
// Angle HIGH press J
// Servo 4
// Angle LOW press alt
// Angle HIGH press space
// Servo 5
// Angle LOW press colon
// Angle HIGH press apostrophe
// Servo 6
// Angle LOW press left
// Angle HIGH press ctrl
// Servo 7
// Angle LOW press right
// Angle HIGH press down


Servo keyToServo (Key key){
   if(key == SPACE){
      return Servo1;
   }
   else if(key == F || key == G){
      return Servo2;
   }
   else if(key == H || key == J){
      return Servo3;
   }
   else if(key == ALT || key == SPACE2){
      return Servo4;
   }
   else if(key == COLON || key == APOS){
      return Servo5;
   }
   else if(key == CTRL || key == LEFT){
      return Servo6;
   }
   else if(key == RIGHT || key == DOWN){
      return Servo7;
   }
   else{
      Serial.println("No servo found");
      Servo errorServo;
      return errorServo;
   }
}

int keyToAngle (Key key){
   if(key == RIGHT){
      return 40;
   }
   else if(key == DOWN){
      return 153;
   }
   else if(key == CTRL){
      return 150;
   }
   else if(key == LEFT){
      return 40;
   }
   else if(key == COLON){
      return 50;
   }
   else if(key == APOS){
      return 130;
   }
   else if(key == F){
      return 60;
   }
   else if(key == G){
      return 125;
   }
   else if(key == H){
      return 55;
   }
   else if(key == J){
      return 125;
   }
   else if(key == ALT){
      return 27;
   }
   else if(key == SPACE){
      return 40;
   }
   else if(key == SPACE2){
      return 130;
   }
   else{
      Serial.println("No keys match");
      return 90;
   }
}
