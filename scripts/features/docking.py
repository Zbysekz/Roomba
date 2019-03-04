#!/usr/bin/python3
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath('__file__'))))
from hardware.roombaPlatform import Platform
from time import sleep
import time
import random
from utils.timer import cTimer

goodDirection = 0
reversing = 0


lastTimeCharging=0
baseIsClose=False
rightBaseBeam=0
leftBaseBeam=0
baseInFront=False
baseInFrontTmr=0
baseDetectedTmr=0
baseLostTmr=0
reverseCounter = 0
lookingForSignal = False #roomba rotates and tries to find good signal
lookingForSignalState=0
totalLostTmr = cTimer()

TOTAL_LOST_TMR=20 # if you dont detect any signal from base for this time,quit docking routine

def Dock(pl):
    global baseIsClose,lastTimeCharging,rightBaseBeam,leftBaseBeam,reversing,goodDirection,baseInFront,baseInFrontTmr
    global baseLost,baseLostTmr,baseDetected,reverseCounter,lookingForSignal,lookingForSignalState,totalLostTmr
        
    leftIRrate = pl.getLeftRate()
    rightIRrate = pl.getRightRate()
    topIRrate = pl.getTopRate()
    
    #print("L:"+str(leftIRrate[0])+","+str(leftIRrate[1])+","+str(leftIRrate[2]))
    #print("R:"+str(rightIRrate[0])+","+str(rightIRrate[1])+","+str(rightIRrate[2]))
    #print("T:"+str(topIRrate[0])+","+str(topIRrate[1])+","+str(topIRrate[2]))
    
    baseIsClose = True if topIRrate[Platform.TOP]>0 else False
    

    if leftBaseBeam > 0:
        leftBaseBeam-=1
    if rightBaseBeam > 0:
        rightBaseBeam-=1
    
        
    #leftBaseBeam = True if topIRrate[Platform.LEFT]>0 else False
    #rightBaseBeam = True if topIRrate[Platform.LEFT]>0 else False
    
    if baseInFront and not pl.isCharging:
        print("BASE IN FRONT!")
    
    baseInFront = baseInFrontTmr > 10
    baseLost = baseLostTmr > 30
    
    if baseLost:
        print("BASE IS LOST!!")
        baseDetected = False
        baseLostTmr = 0
        lookingForSignal = True
        lookingForSignalState = 0
        pl.Move(0,0)
    
    if lookingForSignal:#do not count for base lost, if you are looking for a signal
        baseLostTmr = 0
    
    if not pl.isCharging:
        if pl.baseDetected:
            baseDetected = True
            totalLostTmr.Stop()#if we detect some signal, stop counting totalLost
        else:
            if not totalLostTmr.started:
                totalLostTmr.Start(TOTAL_LOST_TMR)
            if baseDetected and baseLostTmr<100:
                baseLostTmr+=1
    else:
        baseDetected = False
        baseLostTmr = 0
        reverseCounter = 0
        
    # if we are not charging, more middle both signals means that base is in front of you,
    if not pl.isCharging:
        if leftIRrate[Platform.LEFT]+leftIRrate[Platform.RIGHT]>0 and rightIRrate[Platform.LEFT]+rightIRrate[Platform.RIGHT]>0:
            if baseInFrontTmr<30:
                baseInFrontTmr+=1
        elif baseInFrontTmr>0:
            baseInFrontTmr-=1
        

    if not pl.isCharging and not pl.liftedUp and not pl.onCliff: #not pl.somethingClose and           
        
        if reversing>0:
            reversing-=1
        elif pl.bumper:
            print("bumper")
            pl.Move(0,0)
            sleep(1)
            reverseCounter +=1
            
            #but if there was charging signal just before bump, go back a little
            if time.time() - lastTimeCharging < 10:
                pl.Move(-10,-10,distance=15)
                reversing=10
            else:
                pl.Move(-60,-60,distance=40)
                reversing=12
    
    
        elif goodDirection>0:
            goodDirection-=1
            pl.Move(20,20)
            print("KEEPING DIRECTION (F1)")
        elif lookingForSignal:
            print("LOOKING FOR A BASE")
            if lookingForSignalState == 0:
                if pl.standstill:# wait until you stop
                    lookingForSignalState=1
                else:
                    pl.Stop()
                    
            elif lookingForSignalState == 1:
                pl.RotateRandomDir(30,720)#rotate randomly to the left or right
                lookingForSignalState=2
            elif lookingForSignalState == 2:
                if leftIRrate[Platform.LEFT]+leftIRrate[Platform.RIGHT]+rightIRrate[Platform.LEFT]+rightIRrate[Platform.RIGHT]>0:
                    pl.Move(0,0)    
                    print("Found signal when looking (1)")
                    lookingForSignal=False
                elif pl.standstill:
                    pl.Move(0,0) 
                    print("Finished looking without signal (2)")
                    lookingForSignal=False
                    

        elif leftIRrate[Platform.LEFT]==0 and leftIRrate[Platform.RIGHT]!=0 and\
            rightIRrate[Platform.LEFT]==0 and rightIRrate[Platform.RIGHT]!=0:
        
            pl.Move(20,12) #(1)
            print("both only RIGHT - R1")
    
        elif leftIRrate[Platform.LEFT]!=0 and leftIRrate[Platform.RIGHT]==0 and\
            rightIRrate[Platform.LEFT]!=0 and rightIRrate[Platform.RIGHT]==0:
        
            pl.Move(12,20) #(2)
            print("both only LEFT - L2")
        
        #left sensor doesn't see anything but right does
        elif leftIRrate[Platform.LEFT]==0 and leftIRrate[Platform.RIGHT]==0 and\
            (rightIRrate[Platform.LEFT]!=0 or rightIRrate[Platform.RIGHT]!=0):
            
            if rightIRrate[Platform.LEFT] < rightIRrate[Platform.RIGHT]:
                pl.Move(20,12) #(3)
                print("only right sees, more RIGHT - R3")
            else:
                pl.Move(20,12) #(4)
                print("only right sees, more LEFT - R4")
        #right sensor doesn't see anything but left does
        elif rightIRrate[Platform.LEFT]==0 and rightIRrate[Platform.RIGHT]==0 and\
            (leftIRrate[Platform.LEFT]!=0 or leftIRrate[Platform.RIGHT]!=0):
            
            if leftIRrate[Platform.LEFT] > leftIRrate[Platform.RIGHT]:
                pl.Move(12,20) #(5)
                print("only left sees, more left - L5")
            else:
                pl.Move(12,20) #(6)
                print("only left sees, more right - L6")
        elif rightIRrate[Platform.LEFT]!=0 and leftIRrate[Platform.RIGHT]!=0 :
            
                if rightIRrate[Platform.RIGHT] > leftIRrate[Platform.LEFT]:
                    #go slightly right
                    pl.Move(20,18) #(7)
                    print("good dir - F7")
                elif rightIRrate[Platform.RIGHT] < leftIRrate[Platform.LEFT]:
                    #go slightly left
                    pl.Move(18,20)
                    print("good dir - F8")
                else:
                    pl.Move(20,20)
                    print("very good dir F9")
                
                #goodDirection=8
                #print("GOOD DIRECTION!")
#            elif topIRrate[Platform.LEFT]>0:
#                pl.Move(20,10)
#                print("R(10)")
#            elif topIRrate[Platform.RIGHT]>0:
#                pl.Move(10,20)
#                print("L(11)")
        elif not baseInFront and (topIRrate[Platform.LEFT]>0 or topIRrate[Platform.RIGHT]>0):#if nothing else but top sensor
        
            if topIRrate[Platform.LEFT]>0:
                if rightBaseBeam>0:
                    pl.Move(-10,30,distance=10)#base is probably on the left
                    print("TOP left, base probably on left - L(13)")
                    sleep(1)
                else:
                    pl.Move(20,10)
                    print("TOP left - R(10)")
                    leftBaseBeam=40
                    
            elif topIRrate[Platform.RIGHT]>0:
                if leftBaseBeam>0:
                    pl.Move(30,-10,distance=10)#base is probably on the right
                    print("TOP right,base probably on right - R(12)")
                    sleep(1)
                else:
                    rightBaseBeam=40
                    pl.Move(10,20)
                    print("TOP right - L(11)")
        else:
            #if you bumped at least twice and base is close, try turning to find proper angle to base
            if baseIsClose and reverseCounter>=2:
                lookingForSignal=True
                lookingForSignalState=0
                reverseCounter=0
                print("Start looking for signal because too many reverses")
            if baseIsClose:
                pl.Move(15,15)
                print("base is close")
            else:
                pl.Move(30,30)
                print("(-)")
    
    
    else:
        if pl.isCharging:
            lastTimeCharging = time.time()
        pl.Move(0,0)
        #print("(S)"+str(pl.somethingClose)+" "+str(pl.liftedUp) +" "+ str(pl.onCliff))
        
    sleep(0.1)
    
    
    return not totalLostTmr.Expired()#if total lost timer expired, quit docking


if __name__ == "__main__":

    pl = Platform()

    pl.Connect()

    while(1):
        try:
            pl.Preprocess()
            Dock(pl)
            pl.RefreshTimeout()
            
        except KeyboardInterrupt:
            pl.Move(0,0)
            print("Keyboard interrupt, stopping!")
            break
    
    pl.Terminate()
    
    print("END")

        

    
