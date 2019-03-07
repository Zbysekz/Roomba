#!/usr/bin/python3

import smbus
import crc8
from sys import stdout
from time import sleep
from datetime import datetime
from enum import Enum

ADDR_MOTHERBOARD = 0x27      #7 bit address (will be left shifted to add the read write bit)
ADDR_BMS = 0x28

bus=0
LEFT=0
RIGHT=1

errorCntMotherBoard = 0
errorCntBMS = 0
errorCntMotherBoard_CRC = 0
errorCntBMS_CRC = 0

lastMotorLCmd=0
lastMotorRCmd=0

def Init():
    global bus
    bus = smbus.SMBus(1)    # 0 = /dev/i2c-0 (port I2C0), 1 = /dev/i2c-1 (port I2C1)

    try:
        if bus.read_byte_data(ADDR_BMS,0) == 66:
            Log("BMS OK")
        else:
            Log("BMS ERROR!")
            return False
    except OSError:
        Log("BMS ERROR2!");
        return False

    #check communication
    try:
        if bus.read_byte_data(ADDR_MOTHERBOARD,0) == 66:
            Log("Motherboard OK")
        else:
            Log("Motherboard ERROR!")
            return False
    except OSError:
        Log("Motherboard ERROR2!");
        return False
    
    return True
    

def ReadMotherBoardData():
    global errorCntMotherBoard,errorCntMotherBoard_CRC
    try:
        data=[]

        for i in range(1,15):
            data.append(bus.read_byte_data(ADDR_MOTHERBOARD,i))

        rcvCRC = bus.read_byte_data(ADDR_MOTHERBOARD,200)
               
        hash = crc8.crc8()
        hash.update(bytes(data))
        
        crc=int.from_bytes(hash.digest(),byteorder='big')
        if(crc!=rcvCRC):
            Log("CRC mismatch, real:"+str(crc)+" rcvd:"+str(rcvCRC))
            Log(data)
            errorCntMotherBoard_CRC+=1
            return []
    except OSError:
        Log("OSError ReadMotherBoardData()")
        errorCntMotherBoard+=1
        return[]
    
    modif = [Rescale(data[:6]),Rescale(data[6:10]),data[10],data[11]&0x01,(data[11]&0x02)>>1,(data[11]&0x04)>>2,(data[11]&0x08)>>3,(data[11]&0x10)>>4,(data[11]&0x20)>>5,data[12],data[13]]    
    return modif

def Rescale(arr):#rescale 0-255 items in list to 0.0-1.0
    
    for i in range(len(arr)):
       arr[i] = round(arr[i]/255.0,3)#round to 3 decimal places
    
    return arr

def ShowMotherBoardData():
    try:
        while(1):
            data = ReadMotherBoardData()
            if data==[]:
                continue;
            
            stdout.write("\r")
            stdout.write(str(["{0:.3f}".format(i) for i in data[0]]))
            stdout.write("   ")
            stdout.write(str(["{0:.3f}".format(i) for i in data[1]]))
            stdout.write("\t")
            stdout.write(format(str(data[2:]),">30s"))
            stdout.flush()
            sleep(0.1)
    except KeyboardInterrupt:
        stdout.write("\n") # move the cursor to the next line

def Move(leftMotor,rightMotor,ramp=5,stopWhenBump=True,distance=0):
    global errorCntMotherBoard,lastMotorLCmd,lastMotorRCmd
    
    if(leftMotor>100):
        leftMotor=100
    if(rightMotor>100):
        rightMotor=100
    if(leftMotor<-100):
        leftMotor=-100
    if(rightMotor<-100):
        rightMotor=-100
        
    
    lastMotorLCmd = leftMotor
    lastMotorRCmd = rightMotor
    
    if(leftMotor<0):
        leftMotor=256+leftMotor
    if(rightMotor<0):
        rightMotor=256+rightMotor
        
    cmdByte = int(stopWhenBump)<<0
    
    sucess=False
    noOfTries=0
    while(not sucess or noOfTries>2):
        try:
            noOfTries+=1
            
            bus.write_byte_data(ADDR_MOTHERBOARD,1,leftMotor)
            bus.write_byte_data(ADDR_MOTHERBOARD,2,rightMotor)
            bus.write_byte_data(ADDR_MOTHERBOARD,3,cmdByte)
            bus.write_byte_data(ADDR_MOTHERBOARD,4,ramp)
            bus.write_byte_data(ADDR_MOTHERBOARD,5,distance)
            
            hash = crc8.crc8()
            hash.update(bytes([leftMotor,rightMotor,cmdByte,ramp,distance]))
            
                
            crc=int.from_bytes(hash.digest(),byteorder='big')

            bus.write_byte_data(ADDR_MOTHERBOARD,200,crc)
            
            sucess=True
            
        except OSError as inst:
            #Log("OSError in Move()!")
            #Log(type(inst))  
            #Log(inst.args)     
            #Log(inst)
            
            errorCntMotherBoard+=1
            
        if not sucess:
            Log("OSError in Move(), not possible to send!")
            
def getLastMotorCmds():
    return [lastMotorLCmd,lastMotorRCmd]

def Rotate(direction,speed,angle=0,ramp=5):#in degrees
    if direction==LEFT:
        Move(-speed,speed,distance=(int)(angle/180*40),ramp=ramp)
    elif direction==RIGHT:
        Move(speed,-speed,distance=(int)(angle/180*40),ramp=ramp)
    else:
        raise ValueError("Wrong direction parameter")

def BMSgoOff():
    bus.write_byte_data(ADDR_BMS,1,11)
    
    hash = crc8.crc8()
    hash.update(bytes([11]))
    
        
    crc=int.from_bytes(hash.digest(),byteorder='big')

    bus.write_byte_data(ADDR_BMS,200,crc)

def ReadBMSData():
    global errorCntBMS,errorCntBMS_CRC
    try:
        data=[]

        for i in range(1,8):
            data.append(bus.read_byte_data(ADDR_BMS,i))

        rcvCRC = bus.read_byte_data(ADDR_BMS,200)
               
        hash = crc8.crc8()
        hash.update(bytes(data))
        
        crc=int.from_bytes(hash.digest(),byteorder='big')
        if(crc!=rcvCRC):
            Log("CRC mismatch, real:"+str(crc)+" rcvd:"+str(rcvCRC))
            Log(data)
            errorCntBMS_CRC+=1
            return []
        
    except OSError:
        Log("OSError ReadBMSData()")
        errorCntBMS+=1
        return[]
    
    state="normal" if data[0]==0 else "charging" if data[0]==1 else "low" if data[0]==2 else "unknown"

    modif =  [state,(data[1]+data[2]*256)/100,(data[3]+data[4]*256)/100,(data[5]+data[6]*256)/100]    
    
    return modif

def ShowBMSData():
    try:
        while(1):
            
            data = ReadBMSData()
            if data==[]:
                continue;
            stdout.write("\r")
            #stdout.write(format(str(data),">30s"))

            stdout.write(format(data[0]+" cellA:"+str(data[1])+" cellB:"+str(data[2])+" cellC:"+str(data[3]),">40s"))
            stdout.flush()
            sleep(0.1)
    except KeyboardInterrupt:
        stdout.write("\n") # move the cursor to the next line
        
def getErrorCnt():
    return [errorCntMotherBoard, errorCntBMS, errorCntMotherBoard_CRC, errorCntBMS_CRC]

def ResetErrorCnt():
    global errorCntMotherBoard,errorCntBMS,errorCntMotherBoard_CRC,errorCntBMS_CRC
    errorCntMotherBoard=0
    errorCntBMS=0
    errorCntMotherBoard_CRC=0
    errorCntBMS_CRC=0
    
def Log(s):
    print("LOGGED:"+str(s))

    dateStr=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open("logs/comm.log","a") as file:
        file.write(dateStr+" >> "+str(s)+"\n")
