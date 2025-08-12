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

# Writes data to the arduino in 3 byte(char) messages
def write_to_serial(message, ack): 
    # Byte 1: Acknowledgement to tell arduino when message begins
    # Byte 2: Command in ASCII (char)
    # Byte 3: Param in ASCII (char, 1-9)
    data = [ord(ack), ord(message[0]), ord(message[1])]
    arduino.write(data)  

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

    time.sleep(0.35)
    
