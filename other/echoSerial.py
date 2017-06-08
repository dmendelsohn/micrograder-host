import serial
import time

# COM port parameters
ADDR = '/dev/cu.usbmodem1880221'
BAUD = 115200

try:
    port = serial.Serial(ADDR,BAUD)
    #port.write("Beg".encode("ascii"))
    while(1):
        x = port.readline()
        port.write("2".encode("ascii"))
        print(x)
finally:
    port.close()
