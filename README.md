# Automated Game Player
 Arduino(C) + Python program that automatically plays a game for you.
# Includes:
 - Computer Vision that pulls frames from an HDMI connection to a separate controller PC
 - CV that tracks the player location and corrects player positioning by pathfinding to the starting points of the next rotation
 - GUI that provides debugging and status of the bot
 - Keyboard is pressed by servos coordinated using an arduino microcontroller
 - Arduino is loaded with preprogrammed macros for standard actions
 - Serial communication between the main PC and Arduino to send commands based on logic handling done by the controller PC
 - Rotation data of each class saved in JSON to allow modularity for including new classes and new maps 

# Features
 - Program stops when the player opens their inventory to allow for manual control to be taken
 - Separate stop and resume button on the GUI for additional control
 - Rotation index step forward and step backwards to allow for "redoing" failed rotation execution due to special events
 - Special events are highlighted and a sound is played to notify the player
 - Customizable walk speed values and variable double jump delay values for different classes with different double jump animations, distance, and timing
 - Modular design with JSON files allowing the user to add as many rotations as they want for as many classes and maps as they want
 - Classes can have their own rotations for each map
 - Self corrects player positioning when it is thrown off due to lag spikes or special event monsters

# Program in action
https://github.com/user-attachments/assets/261ecac8-e09e-4560-8653-710fe57ce5ed

# Character Swapping in action
https://github.com/user-attachments/assets/705199d5-01bb-43ea-951a-18f4a6b2cde3

# Arduino Setup
![20260225_162108](https://github.com/user-attachments/assets/1bd40d1f-9142-4527-bb42-1e6892d01a60)

# Keyboard servos in action 
https://github.com/user-attachments/assets/163e3e9d-a9f9-4ea4-995f-f169763fccbd


