# Importing Libraries 
import serial 
import time 
import threading
import struct
from datetime import datetime, timedelta
import pdb
import computerVision

arduino = serial.Serial(port='COM3', baudrate=9600, timeout = 1) 
time.sleep(2)

# This is used to convert commands to ASCII for serial communication for arduino
serial_key = {
	"Start Walk" : 'A',
	"End Walk" : 'B',
	"Double Jump": 'C',
	"Double Jump Attack": 'D',
	"Short Double Jump Attack": 'E',
	"Up Jump" : 'F',
	"Up Jump Warrior": 'G',
	"Down Jump": 'H',
	"Use Skill": 'I',
	"Jump Skill": 'J',
	"Swap Keyboard Layout": 'K',
	"Start Hold Attack": 'L',
	"End Hold Attack": 'M',
	"Reset Servos": 'N',
	"Walk Opposite To Double Jump Attack": 'O',
	"Walk Opposite To Short Double Jump Attack": 'P',
	"Walk Short Distance": 'Q',
	"Short Up Jump": 'R',
	"Start Hold Glide": 'S',
	"End Hold Glide": 'T',
	"Up Teleport": 'U',
	"Down Teleport": 'V',
	"Down Jump Flashjump": 'W',
    "Delayed Jump Skill": 'X',
    "Swap Character": 'Y'
}

# Writes data to the arduino in 3 byte(char) messages
def write_to_serial(message, message_type): 
    # === Handshake ===
    print("[Python] Starting handshake...")
    send_and_wait("SYN-ACK", b"SYN\n")
    send_and_wait("READY", b"ACK\n")
    print("[Python] Handshake complete.\n")   
    
    # Byte 1: Message type, command vs settings
    # Byte 2: Command in ASCII (char)
    # Byte 3: Param in ASCII (char, 1-9)
    validate_characters([message_type, message[0], message[1]])
    data = [ord(message_type), ord(message[0]), ord(message[1])]
    arduino.write(data)  

    print(f"[Python] sent Command Type: {message_type}, Command: {inverted_serial_key.get(message[0], message[0])}, Parameter:{message[1]}\n")   

    # If the delay is less than or equal to 3 seconds, we can use a blocking delay
    # If the delay is larger than 3 seconds, use a non-blocking delay
    # Values are in milliseconds
    if message[2] <= 3000:
        time.sleep(message[2]/1000.0)
    else:
        i = 0
        while computerVision.get_is_stopped() == False and i <= message[2]:
            time.sleep(1)
            i += 1000

# === Function: Wait for ack ===
def send_and_wait(expect, send_data=None):
    if send_data:
        arduino.write(send_data)
    while True:
        response = arduino.readline().decode().strip()
        if response == expect:
            print(f"[Python] Received expected: {response}")
            return True
        elif response:
            print(f"[Python] Unexpected response: {response}")

def validate_characters(arr):
    if not all(isinstance(x, str) and len(x) == 1 for x in arr):
        raise ValueError("All elements must be single-character strings.")

# Handle incoming data (button press response)
#def listen_to_arduino():
#    while True:
#       if arduino.in_waiting >= 14:
#            data = arduino.read(arduino.in_waiting)
#            if data:
#                print(f"[Python] Received from Arduino: {data}")

# Start listening thread
#listener_thread = threading.Thread(target=listen_to_arduino, daemon=True)
#listener_thread.start()