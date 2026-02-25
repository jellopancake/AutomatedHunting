# Automated Game Player

 Arduino(C) + Python program that automatically plays a game for you.
# Includes:
 - Computer Vision that allows you to track the player location and correct player positioning by pathfinding to the starting points of the next rotation
 - Keyboard is pressed by servos coordinated using an arduino microcontroller
 - Arduino is loaded with preprogrammed macros for standard actions

Example of a double jump attack macro
<img width="984" height="173" alt="image" src="https://github.com/user-attachments/assets/51845cdd-f6ba-4293-9f20-ffeaf6dfa45e" />

 - Serial communication between the main PC and Arduino to send commands based on logic handling done by the main PC
 - Rotation data saved in JSON for ease of swapping between map and classes

Example of JSON referring to commands with specific parameters (0-1 left or right, 0-5 use a specific skill, these parameters are context sensitive)
<img width="672" height="366" alt="image" src="https://github.com/user-attachments/assets/76d721f8-e659-4c49-bae2-27bcb96371e6" />

# Features
 - Program stops when the player opens their inventory to allow for manual control to be taken
 - Special events are highlighted and a sound is played to notify the player
 - Customizable walk speed values and variable double jump delay values for different classes with different double jump animations, distance, and timing
 - Modular design with JSON files allowing the user to add as many rotations as they want for as many classes and maps as they want
 - Classes can have their own rotations for each map
 - Self corrects player positioning when it is thrown off due to lag spikes or special event monsters

# Arduino Setup
![20260225_162108](https://github.com/user-attachments/assets/1bd40d1f-9142-4527-bb42-1e6892d01a60)

# Keyboard servos in action 
https://github.com/user-attachments/assets/163e3e9d-a9f9-4ea4-995f-f169763fccbd

# Program in action
https://github.com/user-attachments/assets/261ecac8-e09e-4560-8653-710fe57ce5ed

# Character Swapping in action
https://github.com/user-attachments/assets/705199d5-01bb-43ea-951a-18f4a6b2cde3

