#!/usr/bin/python3
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath('__file__'))))
import hardware.comm as comm
import hardware.irm as irm
from sys import stdout
from time import sleep

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
        
    def Connect(self):
        comm.Init()
        irm.Start()
        
    def Preprocess(self):
        self.bmsData = comm.ReadBMSData()

        self.sensorData = comm.ReadMotherBoardData();

        if(self.sensorData ==[] or self.bmsData==[]):
            comm.Move(0,0)
            print("EMPTY DATA!")
            self.validData=False
            return
        
        self.somethingClose = any([s>0.3 for s in self.sensorData[0]])
        
        self.liftedUp = self.sensorData[3]==0 or self.sensorData[4]==0#wheel switches
        
        self.onCliff = any([s<0.3 for s in self.sensorData[1]])
        
        self.isCharging = self.bmsData[0]=='charging'
        
        self.bumper = self.sensorData[6]==0 or self.sensorData[7]==0
        
        self.standstill = self.sensorData[8]!=0 and self.standstillAux==0
        
        if self.standstillAux>0:
            self.standstillAux-=1
        
        self.validData = True
        
    
    def Move(self,leftMotor,rightMotor,ramp=10,stopWhenBump=True,distance=0):
        comm.Move(leftMotor,rightMotor,ramp,stopWhenBump,distance)
        
        if(leftMotor!=0 or rightMotor!=0):
            self.standstill=False
            self.standstillAux=3
        
    def Rotate(self,direction,speed,angle,ramp=5):#in degrees
        comm.Rotate(direction,speed,angle,ramp)

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

        
