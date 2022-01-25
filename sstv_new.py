#!/usr/bin/env/python3
import gpsd
import picamera
import time
from subprocess import run,call
from datetime import datetime
import smbus
import csv
import os
import RPi.GPIO as GPIO
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw
import argparse
import serial

GPIO.setmode(GPIO.BCM)

# Connect to the local gpsd
try:
    gpsd.connect()
except:
   command = "sudo gpsd /dev/serial0 -F /var/run/gpsd.sock"
   run([command, -l])
finally:
   gpsd.connect()

#gpsd.connect(host="127.0.0.1", port=1234)

# Get gps position
# packet = gpsd.get_current()

# See the inline docs for GpsResponse for the available data
# print(packet.position())

CSVHeaders = ["Index", "Time", "Latitude", "Longtitude", "Pressure (kPa)", "Altitude (m)", "Temperature (C)"] 
with open('data.csv', 'w') as f: 
    write = csv.writer(f) 
    write.writerow(CSVHeaders) 
    
def getWeatherData():
    # Distributed with a free-will license.
    # Use it any way you want, profit or free, provided it fits in the licenses of its associated works.
    # MPL3115A2
    # This code is designed to work with the MPL3115A2_I2CS I2C Mini Module
    # Get I2C bus
    bus = smbus.SMBus(1)
    # MPL3115A2 address, 0x60(96)
    # Select control register, 0x26(38)
    # 0xB9(185) Active mode, OSR = 128, Altimeter mode
    bus.write_byte_data(0x60, 0x26, 0xB9)
    # MPL3115A2 address, 0x60(96)
    # Select data configuration register, 0x13(19)
    # 0x07(07) Data ready event enabled for altitude, pressure, temperature
    bus.write_byte_data(0x60, 0x13, 0x07)
    # MPL3115A2 address, 0x60(96)
    # Select control register, 0x26(38)
    # 0xB9(185) Active mode, OSR = 128, Altimeter mode
    bus.write_byte_data(0x60, 0x26, 0xB9)
    time.sleep(1)
    # MPL3115A2 address, 0x60(96)
    # Read data back from 0x00(00), 6 bytes
    # status, tHeight MSB1, tHeight MSB, tHeight LSB, temp MSB, temp LSB
    data = bus.read_i2c_block_data(0x60, 0x00, 6)
    # Convert the data to 20-bits
    tHeight = ((data[1] * 65536) + (data[2] * 256) + (data[3] & 0xF0)) / 16
    temp = ((data[4] * 256) + (data[5] & 0xF0)) / 16
    altitude = tHeight / 16.0
    cTemp = temp / 16.0
    fTemp = cTemp * 1.8 + 32
    # MPL3115A2 address, 0x60(96)
    # Select control register, 0x26(38)
    # 0x39(57) Active mode, OSR = 128, Barometer mode
    bus.write_byte_data(0x60, 0x26, 0x39)
    time.sleep(1)
    # MPL3115A2 address, 0x60(96)
    # Read data back from 0x00(00), 4 bytes
    # status, pres MSB1, pres MSB, pres LSB
    data = bus.read_i2c_block_data(0x60, 0x00, 4)
    # Convert the data to 20-bits
    pres = ((data[1] * 65536) + (data[2] * 256) + (data[3] & 0xF0)) / 16
    pressure = (pres / 4.0) / 1000.0
    # Output data to screen
    # print "Pressure : %.2f kPa" %pressure
    # print "Altitude : %.2f m" %altitude
    # print "Temperature in Celsius : %.2f C" %cTemp
    # print "Temperature in Fahrenheit : %.2f F" %fTemp
    presAltTemp = [pressure, altitude, cTemp]
    return str(presAltTemp)

# Connect to the local gpsd
# gpsd.connect()

# Get gps position
#packet = gpsd.get_current()

# See the inline docs for GpsResponse for the available data
#print(packet.position())

def getPositionData():
    packet = gpsd.get_current()
    latlonString = packet.position()
    return latlonString

def writeCSV(gpsData, weatherData, index):
    timenow = datetime.now()
    # Create file name for our picture
    stringTime = currentTime.strftime("%Y.%m.%d-%H%M%S")
    Row = [index, stringTime, gpsData[0], gpsData[1], weatherData[0], weatherData[1], weatherData[2]]
    with open(r'data.csv', 'a') as f:
        writer = csv.writer(f)



# DRA818 GPIO Connections
DRA818_PTT = 17
# Default Transmitter / Squelch Settings
MODE = 1 # 1 = FM (supposedly 5kHz deviation), 0 = NFM (2.5 kHz Deviation)
SQUELCH = 5 # Squelch Value, 0-8
CTCSS = '0000'

def dra818_program(port='/dev/ttyUSB0',
                frequency=146.500):
    ''' Program a DRA818U/V radio to operate on a particular frequency. '''


    _dmosetgroup = "AT+DMOSETGROUP=%d,%3.4f,%3.4f,%s,%d,%s\r\n" % (
        MODE, frequency, frequency, CTCSS, SQUELCH, CTCSS)

    print("Sending: %s" % _dmosetgroup.strip())

    # Open serial port
    _s = serial.Serial(
            port=port,
            baudrate=9600,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS)
    # We need to issue this command to be able to send further commands.
    _s.write("AT+DMOCONNECT\r\n")
    time.sleep(1.00)
    _response = _s.readline()
    print("Connect Response: %s" % _response)

    # Send the programming command..
    _s.write(_dmosetgroup)
    time.sleep(1.00)

    # Read in the response from the module.
    _response = _s.readline()
    _s.close()
    
    print("Response: %s" % _response.strip())


def dra818_setup_io():
    ''' Configure the RPi IO pins for communication with the DRA818 module '''
    # All pin definitions are in Broadcom format.
    GPIO.setmode(GPIO.BCM)
    # Configure pins, and set initial values.
    GPIO.setup(DRA818_PTT, GPIO.OUT, initial=GPIO.HIGH)


def dra818_ptt(enabled):
    ''' Set the DRA818's PTT on or off '''
    if enabled:
        GPIO.output(DRA818_PTT, GPIO.LOW)
    else:
        GPIO.output(DRA818_PTT, GPIO.HIGH)

filePath = "/home/pi/timestamped_pics/"
picTotal = 50
picCount = 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--frequency", type=float, default=146.500, help="Transmit Frequency (MHz)")
    parser.add_argument("--port", type=str, default='/dev/ttyAMA0', help="Serial port connected to module.")
    parser.add_argument("--test", action="store_true", default=False, help="Test transmitter after programming with 1s of PTT.")
    args = parser.parse_args()

    dra818_program(args.port, args.frequency)

    if args.test:
        dra818_ptt(True)
        time.sleep(1)
        dra818_ptt(False)
        
    while picCount < picTotal:

    # Grab the current time
        currentTime = datetime.now()
    # Create file name for our picture
        picTime = currentTime.strftime("%Y.%m.%d-%H%M%S")
        picName = picTime + '.jpg'
        completeFilePath = filePath + picName

    # Take picture using new filepath
        with picamera.PiCamera() as camera:
            camera.resolution = (320,256) #as specified by sstv format
            camera.capture(completeFilePath)
            print("We have taken a picture.")
        gpsData = getPositionData()
        weatherData = str(getWeatherData())
    # Create our stamp variable
        timestampMessage = currentTime.strftime("%Y.%m.%d - %H:%M:%S")
        newTimestampMessage = timestampMessage + "Lat:" + str(gpsData[0]) + ", Lon:" + str(gpsData[1]) + ", Alt (m):" + weatherData[1]  
    # Create time stamp command to have executed
    # print("Pressure (kPa)" + weatherData[0] + "Altitude (m)" + weatherData[1] + "Temp (C)" + weatherData[2])
    #newTimestampMessage = "'{}'".format(newTimestampMessage)
    #print(newTimestampMessage)
        img = Image.open(completeFilePath)
        draw = ImageDraw.Draw(img)
        draw.text((0,0), newTimestampMessage, (255,255,255))
        img.save(completeFilePath)
    #stringJunk = "drawtext:text='"+newTimestampMessage+"':fontcolor=white:fontsize=24:box=1:boxcolor=black@0.4:boxborderw=5:x=(w-text_w)/2:y=(h-text_h)/2"
    #timestampCommand = 'ffmpeg -i {} -vf "{}" {} -y'.format(completeFilePath,stringJunk,completeFilePath)
    # Actually execute the command!
    # python2: call([timestampCommand], shell=True)
    # run([timestampCommand,"-l"])
        print("We have timestamped our picture!")
        writeCSV(gpsData, weatherData, picCount)
        print("Written to CSV")    
        picCount += 1
        time.sleep(2)         

    #convert pic to sstv using pi-sstv
    #first change directories because I don't know how else to do it
    #os.chdir("/home/pi/pi-sstv/")
    #time.sleep(1)
        pisstvCommand = "/home/pi/pi-sstv/pi-sstv {} 22050".format(completeFilePath)
    #rename commands so we don't have 10,000 sound files. change directory while we're at it
    #os.chdir("/home/pi")
        renameCommand = "mv {}.wav /home/pi/timestamped_pics/sstv.wav".format(completeFilePath)
    #execute commands
        call(pisstvCommand, shell=True)
        call(renameCommand, shell=True) 
        time.sleep(5)
    #transmit the image
        dra818_ptt(True)
		# Delay slightly.
		sleep(0.5)
		self.debug_message("Transmitting...")
		tx_command = "aplay %s" % "/home/pi/timestamped_pics/sstv.wav"
		return_code = os.system(tx_command)
        dra818_ptt(False)
