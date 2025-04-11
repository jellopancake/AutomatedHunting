// Include the Servo library 
#include <Servo.h>

// Declare the Servo pin 
int servo_down_right = 3;
int servo_ctrl_left = 4;
int servo_alt_space = 5;
int servo_X_C = 6;
int servo_alt_space_2 = 7;

// Declare the start/stop button pin
int button_start_stop = 2;


// Tracks whether an update has been made to start/stop the procedure following the reading that the start/stop button has been pressed
// This allows the button to function as a toggle button
// 0 is no update needed, 1 is button has been pressed waiting for update
int start_stop_updated = 0;

int stop_program = 0;

enum Key{LEFT, RIGHT, DOWN, F, G, ALT, CTRL, SPACE, SPACE2};
   Key left = LEFT;
   Key right = RIGHT;
   Key down = DOWN;
   Key jump = SPACE;
   Key altJump = SPACE2;
   Key skill1 = CTRL;
   Key fountain = ALT;
   Key mainAttack = F;
   Key ropelift = G;


// Create a servo object 
Servo Servo1, Servo2, Servo3, Servo4, Servo5; 
void setup() { 
   // open serial port at 9600 bps
   Serial.begin(9600);
   while(!Serial);

   // We need to attach the servo to pins 3-7
   Servo1.attach(servo_alt_space_2); 
   Servo2.attach(servo_X_C); 
   Servo3.attach(servo_alt_space); 
   Servo4.attach(servo_ctrl_left); 
   Servo5.attach(servo_down_right); 

   // Attach start/stop button to pin 2
   pinMode(button_start_stop, INPUT_PULLUP);

   // Initialize in horizontal position
   Servo1.write(90);
   Servo2.write(90);
   Servo3.write(90);
   Servo4.write(90);
   Servo5.write(90);
}

void loop(){ 

   while(stop_program == 0){
      

      // Mobbing Rotation
      for(int i = 0; i < 2; i++){
         flatMobbingRotation(left, 5);
         
         if(start_stop_updated == 1){
            break;
         }
         flatMobbingRotation(right, 5);

         if(start_stop_updated == 1){
            break;
         }
      }
      if(start_stop_updated == 1){
         stopProgram();
         break;
      }
     
      // Loot rotation
      delay(300);
      doubleJumpAttackOnce(left);
      ropeLift();
      pressButton(mainAttack);
      placeSummon();
      useSkill1();
      jumpAttack(left);      
      walk(right, 1.5);
      ropeLift();
      doubleJumpAttackOnce(left);
      walk(left, 1.3);
      downJump();
      delay(200);
      shortDoubleJumpAttack(left);
      doubleJumpAttackOnce(left);
      walk(left, 0.7);
      downJump();
      walk(left, 0.9);
      shortDoubleJumpAttack(right);
      loopDoubleJumpAttack(right, 2);
      walk(right, 1.1);
      doubleJumpAttackOnce(right);
      walkAttack(left, 1);
      doubleJumpAttackOnce(right);
      delay(100);

      if(start_stop_updated == 1){
         stopProgram();
         break;
      }
      
   }

   checkStartStop();
   delay(500);
   if(start_stop_updated == 1){
      startProgram();
   }
}

// Preset inputs //////////////////////////////////////////////////////////////////////////////////////////////////

void flatMobbingRotation(Key dir, int repeatCount){
   // Use a variable to check if we do the random single jump attack, 
   // if so we compensate the extra distance gained by doing a short double jump
   int randomJump = 0;
   
   if(random(1, 100) >= 50){
      walk(dir, random(600, 700)/1000.0);
   } else{
      walk(dir, random(300, 400)/1000.0);
      delay(100);
      jumpAttack(dir);
      delay(200);
      randomJump = 1;
   }

   delay(200);

   if(dir == left){
      if(randomJump == 0){
         doubleJumpAttackOnce(left);
      }
      else{
         shortDoubleJumpAttack(left);
      }
      ropeLift();
      jumpAttack(left);
      shortDoubleJumpAttack(right);
      downJump();
      loopDoubleJumpAttack(dir, repeatCount-3);
      walk(left, 0.7);
      doubleJumpAttackOnce(dir);
      shortDoubleJumpAttack(dir);
      downJump();
      
   }
   else{
      loopDoubleJumpAttack(dir, repeatCount);
      delay(100);
   }
}

// Places down erda fountain
void placeSummon(){
   delay(500);
   pressButton(fountain);
   delay(500);
}

// Walks in a given direction while attacking
void walkAttack(Key dir, float holdTime){
   holdButton(dir, holdTime/2);
   pressButton(mainAttack);
   holdButton(dir, holdTime/2);
}

// Loops flashjump attack with a given number of repeats and chosen delay
void loopDoubleJumpAttack(Key dir, int repeatCount){
   pressDownButton(dir);
   for (int i = 0; i < repeatCount; i++) {
      doubleJumpAttack(dir);
      delay(230);
   }
   resetButton(dir);
}

// Performs a single flashjump in a given direction with an attack, while specifically holding down a direction button
void doubleJumpAttackOnce(Key dir){
   pressDownButton(dir);
   doubleJumpAttack(dir);
   resetButton(dir);
   delay(200);
}

// Performs a flashjump in a given direction with an attack
void doubleJumpAttack(Key dir){
   delay(100);
   pressButton(altJump);
   delay(125);
   pressDownButton(jump);
   delay(100);
   pressButton(mainAttack);
   resetButton(jump);
   delay(100);
}

// Performs a shorter flashjump in a given direction with an attack
void shortDoubleJumpAttack(Key dir){
   pressDownButton(dir);
   delay(400);
   pressButton(altJump);
   delay(350);
   pressDownButton(jump);
   delay(100);
   pressDownButton(mainAttack);
   delay(350);
   resetButton(mainAttack);
   resetButton(jump);
   resetButton(dir);
   delay(250);
}

// Performs a flashjump in a given direction
void doubleJump(Key dir){
   pressButton(altJump);
   delay(200);
   pressButton(jump);
   delay(200);   
}

// Walks in a given direction
void walk(Key dir, float holdTime){
   holdButton(dir, holdTime);
}

// Performs a jump in a given direction with an attack
void jumpAttack(Key dir){
   pressDownButton(dir);
   delay(200);
   pressButton(jump);
   pressButton(mainAttack);
   resetButton(dir);

}

// Uses skill1
void useSkill1(){
   delay(500);
   pressButton(skill1);
   delay(1000);
}

// Performs ropelift to bring the character to the highest platform above it
void ropeLift(){
   delay(600);
   pressButton(ropelift);
   delay(1300);
}

// Performs a downjump to bring the character one platform below it
void downJump(){
   delay(200);
   pressDownButton(down);
   delay(300);
   pressButton(jump);
   delay(200);
   resetButton(down);
   delay(300);
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

void resetButton(Key key){
   Servo servo = keyToServo(key);
   
   servo.write(90);
}

// Start/Stop functionality ///////////////////////////////////////////////////////////////////////

// Checks if the start/stop button is pressed
void checkStartStop(){
   if(digitalRead(button_start_stop) == 0 && start_stop_updated == 0){
      start_stop_updated = 1;
   }
}

// Stops the current mobbing rotation and resets servos to starting positions and fulfills the update required by the start/stop button
void stopProgram(){
   Servo1.write(90);
   Servo2.write(90);
   Servo3.write(90);
   Servo4.write(90);
   Servo5.write(90);
   
   start_stop_updated = 0;
   stop_program = 1;
   delay(1000);
}

// Restarts the mobbing rotation and moves the character to the starting position and fulfills the update required by the start/stop button
void startProgram(){
   flatMobbingRotation(right, 5);

   start_stop_updated = 0;
   stop_program = 0;
   delay(1000);
}

// Servo Legend for angles required to press keyboard keys //////////////////////////////////////////////////////////////////////////////////////////////////
// Servo 1
// Angle 40 press right
// Angle 150 press down
// Servo 2
// Angle 40 press left
// Angle 150 press ctrl
// Servo 3
// Angle 20 press alt
// Angle 150 press space
// Servo 4
// Angle 40 press F
// Angle 140 press G
// Servo 5
// Angle 30 press space
// Angle 160 press alt

Servo keyToServo (Key key){
   checkStartStop();
   if(key == RIGHT || key == DOWN){
      return Servo1;
   }
   else if(key == CTRL || key == LEFT){
      return Servo2;
   }
   else if(key == ALT || key == SPACE2){
      return Servo3;
   }
   else if(key == F || key == G){
      return Servo4;
   }
   else if(key == SPACE){
      return Servo5;
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
      return 150;
   }
   else if(key == CTRL){
      return 150;
   }
   else if(key == LEFT){
      return 40;
   }
   else if(key == F){
      return 40;
   }
   else if(key == G){
      return 140;
   }
   else if(key == ALT){
      return 20;
   }
   else if(key == SPACE){
      return 40;
   }
   else if(key == SPACE2){
      return 140;
   }
   else{
      Serial.println("No keys match");
      return 90;
   }
}