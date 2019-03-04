#!/usr/bin/python3
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(sys.argv[0]))))

import hardware.comm as comm
import hardware.irm as irm
from sys import stdout
from time import sleep
import random
import RPi.GPIO as GPIO

PIN_FAN = 16# fan in stack
PIN_SWEEPER = 21#sweeper
PIN_BRUSH = 20# main brush

GPIO.setmode(GPIO.BCM)
GPIO.setup(PIN_FAN, GPIO.OUT)
GPIO.setup(PIN_SWEEPER, GPIO.OUT)
GPIO.setup(PIN_BRUSH, GPIO.OUT)

class Platform:
    LEFT = 0
    RIGHT = 1
    TOP = 2
    
    def __init__(self):
        self.bmsData=[]
        self.sensorData=[]
        self.somethingClose=False
        self.liftedUp=False
        self.onCliff=False
        self.validData=False
        self.isCharging=False
        self.standstill=False
        self.standstillAux=0
        self.baseDetected=False
        
        self.StopCleaningMotors()
        
    def Connect(self):
        comm.Init()
        irm.Start()
        
    def Preprocess(self):
        self.bmsData = comm.ReadBMSData()

        self.sensorData = comm.ReadMotherBoardData();

        if(self.sensorData ==[] or self.bmsData==[]):
            #comm.Move(0,0)
            print("EMPTY DATA!")
            self.validData=False
            return
        
        leftIRrate = self.getLeftRate()
        rightIRrate = self.getRightRate()
        topIRrate =self.getTopRate()
    
        self.baseDetected = (leftIRrate[Platform.RIGHT]+leftIRrate[Platform.LEFT]+leftIRrate[Platform.TOP]+\
        rightIRrate[Platform.RIGHT]+rightIRrate[Platform.LEFT]+rightIRrate[Platform.TOP]+\
        topIRrate[Platform.RIGHT]+topIRrate[Platform.LEFT]+topIRrate[Platform.TOP])>3
        
        self.batVoltages = [self.bmsData[1],self.bmsData[2],self.bmsData[3]]
        
        self.veryLowBattery = any([v<3.3 for v in self.batVoltages])
        self.lowBattery = any([v<3.5 for v in self.batVoltages])
        
        
        self.somethingClose = any([s>0.3 for s in self.sensorData[0]])
        
        self.liftedUp = self.sensorData[3]==0 or self.sensorData[4]==0#wheel switches
        
        self.onCliff = any([s<0.15 for s in self.sensorData[1]])
        
        self.isCharging = self.bmsData[0]=='charging'
        
        self.bumper = self.sensorData[6]==0 or self.sensorData[7]==0
        
        self.standstill = self.sensorData[8]!=0 and self.standstillAux==0
        
        if self.standstillAux>0:
            self.standstillAux-=1
        
        self.validData = True
        
    def getDynamicSpeed(self,minSpeed,maxSpeed): #return speed accoring to obstacles in front of roomba
        
        if not self.validData:
            return minSpeed
        
        speed = maxSpeed
        
        if any([s>0.3 for s in self.sensorData[0][0:5]]):#take all six sensors
            speed = minSpeed
        elif any([s>0.2 for s in self.sensorData[0][1:4]]):
            speed = (maxSpeed - minSpeed)/2 + minSpeed
        elif any([s>0.1 for s in self.sensorData[0][2:3]]):
            speed = (maxSpeed - minSpeed)*3/4 + minSpeed
        
        return int(speed)
    
    def Move(self,leftMotor,rightMotor,distance=0,ramp=200,stopWhenBump=True):
        comm.Move(leftMotor,rightMotor,ramp,stopWhenBump,distance)
        
        if(leftMotor!=0 or rightMotor!=0):
            self.standstill=False
            self.standstillAux=3
        
    def Rotate(self,direction,speed,angle=0,ramp=200):#in degrees
        comm.Rotate(direction,speed,angle,ramp)
        self.standstill=False
        self.standstillAux=3
    def RotateRandomDir(self,speed,angle=0,ramp=200):#randomly choose direction to rotate
        self.Rotate(self.LEFT if bool(random.randint(0,1))else self.RIGHT,speed,angle,ramp)
        
    def RotateRandomDirAngle(self,speed,angleMin=30,angleMax=180,ramp=200):#randomly choose direction and angle to rotate
        self.Rotate(self.LEFT if bool(random.randint(0,1))else self.RIGHT,speed,random.randint(angleMin,angleMax),ramp)

    def Stop(self):
        self.Move(0,0)

    def Terminate(self):
        irm.Terminate()
        
    def RefreshTimeout(self):
        irm.tmrTimeout.value=300

    def getLeftRate(self):
        return irm.getLeftRate()
    def getRightRate(self):
        return irm.getRightRate()
    def getTopRate(self):
        return irm.getTopRate()
    
    def PrintErrorCnt(self):
        print("ERROR STATS:"+str(comm.getErrorCnt()))
        #comm.ResetErrorCnt()
    
    def StartCleaningMotors(self):
        self.cleaningMotors=True
        GPIO.output(PIN_FAN, GPIO.HIGH)
        GPIO.output(PIN_SWEEPER, GPIO.HIGH)
        GPIO.output(PIN_BRUSH, GPIO.HIGH)
        
    def StopCleaningMotors(self):
        self.cleaningMotors=False
        GPIO.output(PIN_FAN, GPIO.LOW)
        GPIO.output(PIN_SWEEPER, GPIO.LOW)
        GPIO.output(PIN_BRUSH, GPIO.LOW)
        
    def getCleaningMotorsState(self):
        return self.cleaningMotors

if __name__ == "__main__":   

    comm.Init();

    if(len(sys.argv)>1):
        if('BMS' in sys.argv[1]):
            comm.ShowBMSData()
        elif('MOTHER' in sys.argv[1]):
            comm.Move(0,0)
            comm.ShowMotherBoardData()
        elif('IRM' in sys.argv[1]):
            irm.Start()
            
            try:
                while(True):
                    irm.tmrTimeout.value=300
                    irm.time.sleep(5)
            except KeyboardInterrupt:
                print("Keyboard interrupt, stopping!")
    
            print("TERMINATING")
            irm.Terminate()
        elif('OFF' in sys.argv[1]):
            print("Shutting down BMS and raspberry")
            comm.BMSgoOff()
            from subprocess import call
            call("shutdown -h now", shell=True)
        
