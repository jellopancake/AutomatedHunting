# Importing Libraries 
import serial 
import time 
import threading
import struct

import pdb

serial_buffer = [None, None]

arduino = serial.Serial(port='COM5', baudrate=9600, timeout = 1) 
time.sleep(2)

# Writes data to the arduino in 3 byte(char) messages
def write_to_serial(message, ack): 
    # Byte 1: Acknowledgement to tell arduino when message begins
    # Byte 2: Command in ASCII (char)
    # Byte 3: Param in ASCII (char, 1-9)
    data = [ord(ack), ord(message[0]), ord(message[1])]
    arduino.write(data)  

    # Wait time given in the JSON file
    time.sleep(message[2]/1000.0)
    time.sleep(0.8)
    
def clear_serial_buffer():
    global serial_buffer 
    serial_buffer = [None, None]
