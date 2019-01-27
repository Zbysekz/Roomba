#!/usr/bin/python3

import comm
from sys import stdout
import sys
from time import sleep
import irm

#def RunLogic():
#    try:
#        while(1):
#            bmsData = ReadBMSData()
#
#            sensorData = ReadMotherBoardData();
#
#            if(sensorData ==[] or bmsData==[]):
#                Move(0,0)
#                print("EMPTY DATA!")
#                sleep(1)
#                continue
#            
#            somethingClose = any([s>0.3 for s in sensorData[0]])
#            
#            liftedUp = not sensorData[3]!=0 or not sensorData[4]!=0#wheel switches
#            
#            onCliff = any([s<0.5 for s in sensorData[1]])
#
#            print(str(sensorData[0])+" --- "+str(somethingClose)+" "+str(liftedUp)+" "+str(onCliff))
#            if not somethingClose and not liftedUp and not onCliff:
#                Move(40,40)
#            else:
#                Move(0,0)
#            
#            sleep(0.05)
#    except KeyboardInterrupt:
#        Move(0,0)
#        print("Keyboard interrupt, stopping!")

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
        
    def Connect(self):
        comm.Init()
        irm.Start()
        
    def Preprocess(self):
        self.bmsData = comm.ReadBMSData()

        self.sensorData = comm.ReadMotherBoardData();

        if(self.sensorData ==[] or self.bmsData==[]):
            comm.Move(0,0)
            print("EMPTY DATA!")
            return
        
        self.somethingClose = any([s>0.3 for s in self.sensorData[0]])
        
        self.liftedUp = self.sensorData[3]==0 or self.sensorData[4]==0#wheel switches
        
        self.onCliff = any([s<0.5 for s in self.sensorData[1]])
        
        self.isCharging = self.bmsData[0]=='charging'
        
        self.bumper = self.sensorData[6]==0 or self.sensorData[7]==0
        
    
    def Move(self,leftMotor,rightMotor,ramp=10,stopWhenBump=True,distance=0):
        comm.Move(leftMotor,rightMotor,ramp,stopWhenBump,distance)
        
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

        