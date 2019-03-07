#!/usr/bin/python3
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath('__file__'))))#adds parent directory to path
from hardware.roombaPlatform import Platform
from time import sleep
from datetime import datetime
import time

afterBump = False

def WallFollowing(pl):
    global afterBump,tmrBump


    if pl.isCharging or pl.liftedUp or pl.onCliff or not pl.validData:#not pl.somethingClose and  
        pl.Move(0,0)
        Log("STOP:"+str(pl.isCharging)+" "+str(pl.liftedUp)+" "+str(pl.onCliff)+" "+str(pl.validData))
    elif afterBump>0:
        Log("afterBump:"+str(afterBump))

        if afterBump==1 and pl.standstill:
            afterBump=0
        elif afterBump==2 and pl.standstill:
            pl.Move(-30,30,distance=10)
            afterBump=10
        elif afterBump==10 and pl.standstill:
            afterBump=0
        
    elif pl.bumper:
        if pl.sensorData[7]==0:#if we hit by right bumper
            afterBump=1
            pl.Move(-30,-10,distance=10)
        if pl.sensorData[6]==0:# if we hit by left bumper
            afterBump=2
            pl.Move(-20,-20,distance=10)
        
    else:          
        
        sideSensors = pl.sensorData[0]

        steer = 0

        steer += sideSensors[2] if sideSensors[2]>0.3 else 0
        steer += sideSensors[3] if sideSensors[3]>0.3 else 0
        
        steer += sideSensors[4] if sideSensors[4]>0.1 else 0
        steer += sideSensors[5] - 0.7

        #limit steering value
        maxSteerL=0.8
        maxSteerR=0.8
        if steer>maxSteerL:
            steer=maxSteerL
        elif steer<-maxSteerR:
            steer=-maxSteerR
            
        Log(sideSensors)
        Log("steer:"+str(steer))

        pl.Move(40-int((steer)*50),45+int((steer)*50),ramp=200)   #more steer means more to the LEFT
        
        
    sleep(0.1)
    
def Log(s):
    print("LOGGED:"+str(s))

    dateStr=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open("logs/wallFollowing.log","a") as file:
        file.write(dateStr+" >> "+str(s)+"\n")


if __name__ == "__main__":

    pl = Platform()

    pl.Connect()

    while(1):
        try:
            pl.Preprocess()
            WallFollowing(pl)
            pl.RefreshTimeout()
        except KeyboardInterrupt:
            pl.Move(0,0)
            Log("Keyboard interrupt, stopping!")
            break
    
    pl.Terminate()
    
    Log("END")

        

    
