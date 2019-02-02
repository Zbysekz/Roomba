#!/usr/bin/python3
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
from hardware.roombaPlatform import Platform
from time import sleep
import time

afterBump = False
tmrBump=0

def WallFolowing(pl):
            

    if afterBump>0:

        if afterBump==1 and time.time()-tmrBump > 3:
            afterBump=0
        elif afterBump==2 and time.time()-tmrBump > 3:
            Move(30,-30,distance=20)
            afterBump=10
            tmrBump=time.time()
        elif afterBump==10 and time.time()-tmrBump > 3:
            afterBump=0
        
    elif pl.bumper:
        tmrBump=time.time()
        if sensorData[6]==0:
            afterBump=1
            Move(-10,-30,distance=20)
        if sensorData[7]==0:
            afterBump=2
            Move(-20,-20,distance=20)
        
    elif not pl.isCharging and not pl.liftedUp and not pl.onCliff: #not pl.somethingClose and           
        
        sideSensors = pl.sensorData[0]

        steer = 0

        steer += sideSensors[0]
        steer += sideSensors[1]
        steer += sideSensors[2]
        steer += sideSensors[3]

        #normalize steer to 0 - 1.0
        steer = steer / 4

        Move(50,50-int(steer*100),ramp=200)
        
    
    else:
        pl.Move(0,0)
        
    sleep(0.1)
    


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
            print("Keyboard interrupt, stopping!")
    
    pl.Terminate()
    
    print("END")

        

    
