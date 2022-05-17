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
GPIO.cleanup()
# Connect to the local gpsd
try:
    gpsd.connect()
except:
   command = "sudo gpsd /dev/serial0 -F /var/run/gpsd.sock"
   os.system(command)
finally:
   gpsd.connect()

CSVHeaders = ["Index", "Time", "Latitude", "Longtitude", "Pressure (kPa)", "Altitude (m)", "Temperature (C)"] 
with open('data.csv', 'a') as f: 
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
    return presAltTemp

# Connect to the local gpsd
# gpsd.connect()

# Get gps position
#packet = gpsd.get_current()

# See the inline docs for GpsResponse for the available data
#print(packet.position())

def getPositionData():
    try:
        packet = gpsd.get_current()
        latlonString = packet.position()
    except:
        latlonString = [0,0]
    return latlonString

def writeCSV(gpsData, weatherData, index):
    timenow = datetime.now()
    # Create file name for our picture
    stringTime = currentTime.strftime("%Y.%m.%d-%H%M%S")
    Row = [index, stringTime, gpsData[0], gpsData[1], weatherData[0], weatherData[1], weatherData[2]]
    with open(r'/home/pi/data.csv', 'a') as f:
        writer = csv.writer(f)
        writer.writerow(Row)


# DRA818 GPIO Connections
DRA818_PTT = 27
DRA818_PD = 4
DRA818_HL = 22
GPIO.setup(DRA818_PTT, GPIO.OUT, initial=GPIO.HIGH) 
GPIO.setup(DRA818_HL, GPIO.OUT, initial=GPIO.LOW) # High or low power
GPIO.setup(DRA818_PD, GPIO.OUT, initial=GPIO.LOW) # Go to sleep

filePath = "/home/pi/timestamped_pics/"
picTotal = 500
picCount = 0


if __name__ == '__main__':
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
            try:
                camera.capture(completeFilePath)
            except:
                completeFilePath = "/home/pi/pi-sstv/test_image.png"
            print("We have taken a picture.")
        gpsData = getPositionData()
        weatherData = getWeatherData()
        # Create our stamp variable
        timestampMessage = currentTime.strftime("%Y.%m.%d - %H:%M:%S")
        newTimestampMessage = "Lat:" + str(gpsData[0]) + ", Lon:" + str(gpsData[1])
        timestamp2 =  "Alt (m):" + str(weatherData[1]) + ", Temp (C):" + str(weatherData[2])  
        # Create time stamp command to have executed
        # print("Pressure (kPa)" + weatherData[0] + "Altitude (m)" + weatherData[1] + "Temp (C)" + weatherData[2])
        #newTimestampMessage = "'{}'".format(newTimestampMessage)
        #print(newTimestampMessage)
        img = Image.open(completeFilePath)
        font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
        font = ImageFont.truetype(font_path, 14)
        font2 = ImageFont.truetype(font_path,24)
        # draw.text((5, 5), char, (0,0,0),font=font)
        draw = ImageDraw.Draw(img)
        draw.text((0,0), timestampMessage, (255,255,255), font=font) # time
        draw.text((0,20), newTimestampMessage, (255,255,255), font=font) # lat/lon
        draw.text((0,40),timestamp2,(255,255,255), font=font) #altitude/temp
        imgSequence = "W2KGY 2022 HAB IMG: " + str(picCount)
        draw.text((0,200), imgSequence, (255,255,255), font=font2)
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
        time.sleep(10) # take a picture every 10 seconds except when transmitting    

        if picCount % 12 == 0 or picCount == 1: # transmit with break of 2 minutes
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
            time.sleep(0.5)
            # play the audio through the GPIO Pins
            GPIO.output(DRA818_PD, GPIO.HIGH) #wake up
            time.sleep(1)
            GPIO.output(DRA818_PTT, GPIO.LOW)
            time.sleep(0.1)
            #call("cd", shell=True)
            playCommand = "aplay /home/pi/timestamped_pics/sstv.wav"
            call(playCommand,shell = True)
            time.sleep(0.5) # see if this acutally does anything - keep it
            # time.sleep(0.1)
            GPIO.output(DRA818_PTT, GPIO.HIGH)
            GPIO.output(DRA818_PD, GPIO.LOW) #go back to sleep

