# Importing Libraries 
import serial 
import time 
import threading
import struct

import pdb

serial_buffer = [None, None]

arduino = serial.Serial(port='COM5', baudrate=9600, timeout = 1) 
time.sleep(2)

def write_to_serial(message, ack): 
    data = [ord(ack), ord(message[0]), ord(message[1])]
    arduino.write(data)  
    time.sleep(message[2]/1000.0)
    time.sleep(1)
    
def clear_serial_buffer():
    global serial_buffer 
    serial_buffer = [None, None]
