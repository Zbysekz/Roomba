#!/usr/bin/python3
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath('__file__'))))
from hardware.roombaPlatform import Platform
from time import sleep
from datetime import datetime
import time
import random
from utils.timer import cTimer

goodDirection = 0
reversing = 0

tmr100ms = cTimer()

lastTimeCharging=0
baseIsClose=False
rightBaseBeam=0
leftBaseBeam=0
baseInFront=False
baseInFrontTmr=0
baseLostTmr=0
reverseCounter = 0
lookingForSignal = False #roomba rotates and tries to find good signal
lookingForSignalState=0
totalLostTmr = cTimer()
goBackAndTryAgain= False
TOTAL_LOST_TMR=20 # if you dont detect any signal from base for this time,quit docking routine

def Dock(pl):
    global baseIsClose,lastTimeCharging,rightBaseBeam,leftBaseBeam,reversing,goodDirection,baseInFront,baseInFrontTmr
    global baseLost,baseLostTmr,baseDetected,reverseCounter,lookingForSignal,lookingForSignalState,totalLostTmr,tmr100ms
    global goBackAndTryAgain
        
    leftIRrate = pl.getLeftRate()
    rightIRrate = pl.getRightRate()
    topIRrate = pl.getTopRate()
    
    #Log("L:"+str(leftIRrate[0])+","+str(leftIRrate[1])+","+str(leftIRrate[2]))
    #Log("R:"+str(rightIRrate[0])+","+str(rightIRrate[1])+","+str(rightIRrate[2]))
    #Log("T:"+str(topIRrate[0])+","+str(topIRrate[1])+","+str(topIRrate[2]))
    
    baseIsClose = True if topIRrate[Platform.TOP]>0 else False
    
    if tmr100ms.Expired() or not tmr100ms.started:
        tmr100ms.Start(0.1)
        puls100ms=True
    else:
        puls100ms=False

    if leftBaseBeam > 0 and puls100ms:
        leftBaseBeam-=1
    if rightBaseBeam > 0 and puls100ms:
        rightBaseBeam-=1
        
    
    
        
    #leftBaseBeam = True if topIRrate[Platform.LEFT]>0 else False
    #rightBaseBeam = True if topIRrate[Platform.LEFT]>0 else False
    
    if baseInFront and not pl.isCharging:
        Log("BASE IN FRONT!")
    
    baseInFront = baseInFrontTmr > 20
    baseLost = baseLostTmr > 70
    
    if baseLost:
        Log("BASE IS LOST!!")
        baseDetected = False
        baseLostTmr = 0
        lookingForSignal = True
        lookingForSignalState = 0
        pl.Move(0,0)
    
    if lookingForSignal:#do not count for base lost, if you are looking for a signal
        baseLostTmr = 0
        
    if baseInFront:
        reverseCounter=0
    
    if not pl.isCharging:
        if pl.baseDetected:
            baseDetected = True
            totalLostTmr.Stop()#if we detect some signal, stop counting totalLost
        else:
            if not totalLostTmr.started:
                totalLostTmr.Start(TOTAL_LOST_TMR)
            if baseDetected and baseLostTmr<100 and puls100ms:
                baseLostTmr+=1
    else:
        baseDetected = False
        baseLostTmr = 0
        reverseCounter = 0
        
    # if we are not charging, more middle both signals means that base is in front of you,
    if not pl.isCharging:
        if leftIRrate[Platform.LEFT]+leftIRrate[Platform.RIGHT]>0 and rightIRrate[Platform.LEFT]+rightIRrate[Platform.RIGHT]>0:
            if baseInFrontTmr<30 and puls100ms:
                baseInFrontTmr+=1
        elif baseInFrontTmr>0 and puls100ms:
            baseInFrontTmr-=1
        

    if not pl.isCharging and not pl.liftedUp and not pl.onCliff: #not pl.somethingClose and           
        
        if reversing>0:
            if(puls100ms):
                reversing-=1
        elif goBackAndTryAgain:
            print("Going back further to try again")
            if pl.standstill:
                goBackAndTryAgain=False
                lookingForSignal=True
                lookingForSignalState=0
                
        elif pl.bumper:
            Log("bumper")
            pl.Move(0,0)
            sleep(1)
            reverseCounter +=1
            
            #if you bumped at least twice and base is close, try turning to find proper angle to base
            if baseIsClose and reverseCounter>2:
                goBackAndTryAgain=True
                reverseCounter=0
                Log("Going more back and start looking for a base because too many reverses")
                pl.Move(-40,-40,distance=100)
                reversing=5
    
            #but if there was charging signal just before bump, go back a little
            elif time.time() - lastTimeCharging < 10:
                pl.Move(-10,-10,distance=15)
                reversing=10
            else:
                pl.Move(-60,-60,distance=40)
                reversing=12
                
        elif goodDirection>0:
            if puls100ms:
                goodDirection-=1
            pl.Move(20,20)
            Log("KEEPING DIRECTION (F1)")
        elif lookingForSignal:
            Log("LOOKING FOR A BASE")
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
                    Log("Found signal when looking (1)")
                    lookingForSignal=False
                elif pl.standstill:
                    pl.Move(0,0) 
                    Log("Finished looking without signal (2)")
                    lookingForSignal=False
                    

        elif leftIRrate[Platform.LEFT]==0 and leftIRrate[Platform.RIGHT]!=0 and\
            rightIRrate[Platform.LEFT]==0 and rightIRrate[Platform.RIGHT]!=0:
        
            pl.Move(20,12) #(1)
            Log("both only RIGHT - R1")
    
        elif leftIRrate[Platform.LEFT]!=0 and leftIRrate[Platform.RIGHT]==0 and\
            rightIRrate[Platform.LEFT]!=0 and rightIRrate[Platform.RIGHT]==0:
        
            pl.Move(12,20) #(2)
            Log("both only LEFT - L2")
        
        #left sensor doesn't see anything but right does
        elif leftIRrate[Platform.LEFT]==0 and leftIRrate[Platform.RIGHT]==0 and\
            (rightIRrate[Platform.LEFT]!=0 or rightIRrate[Platform.RIGHT]!=0):
            
            if rightIRrate[Platform.LEFT] < rightIRrate[Platform.RIGHT]:
                pl.Move(20,12) #(3)
                Log("only right sees, more RIGHT - R3")
            else:
                pl.Move(20,12) #(4)
                Log("only right sees, more LEFT - R4")
        #right sensor doesn't see anything but left does
        elif rightIRrate[Platform.LEFT]==0 and rightIRrate[Platform.RIGHT]==0 and\
            (leftIRrate[Platform.LEFT]!=0 or leftIRrate[Platform.RIGHT]!=0):
            
            if leftIRrate[Platform.LEFT] > leftIRrate[Platform.RIGHT]:
                pl.Move(12,20) #(5)
                Log("only left sees, more left - L5")
            else:
                pl.Move(12,20) #(6)
                Log("only left sees, more right - L6")
        elif rightIRrate[Platform.LEFT]!=0 and leftIRrate[Platform.RIGHT]!=0 :
            
                if rightIRrate[Platform.RIGHT] > leftIRrate[Platform.LEFT]:
                    #go slightly right
                    pl.Move(20,18) #(7)
                    Log("good dir - F7")
                elif rightIRrate[Platform.RIGHT] < leftIRrate[Platform.LEFT]:
                    #go slightly left
                    pl.Move(18,20)
                    Log("good dir - F8")
                else:
                    pl.Move(20,20)
                    Log("very good dir F9")
                
                #goodDirection=8
                #Log("GOOD DIRECTION!")
#            elif topIRrate[Platform.LEFT]>0:
#                pl.Move(20,10)
#                Log("R(10)")
#            elif topIRrate[Platform.RIGHT]>0:
#                pl.Move(10,20)
#                Log("L(11)")
        elif not baseInFront and (topIRrate[Platform.LEFT]>0 or topIRrate[Platform.RIGHT]>0):#if nothing else but top sensor
        
            if topIRrate[Platform.LEFT]>0:
                if rightBaseBeam>0:
                    pl.Move(-10,30,distance=10)#base is probably on the left
                    Log("TOP left, base probably on left - L(13)")
                    sleep(1)
                else:
                    pl.Move(20,10)
                    Log("TOP left - R(10)")
                    leftBaseBeam=40
                    
            elif topIRrate[Platform.RIGHT]>0:
                if leftBaseBeam>0:
                    pl.Move(30,-10,distance=10)#base is probably on the right
                    Log("TOP right,base probably on right - R(12)")
                    sleep(1)
                else:
                    rightBaseBeam=40
                    pl.Move(10,20)
                    Log("TOP right - L(11)")
        else:
            if baseIsClose:
                pl.Move(15,15)
                Log("base is close")
            else:
                pl.Move(30,30)
                Log("(-)")
    
    
    else:
        if pl.isCharging:
            lastTimeCharging = time.time()
        pl.Move(0,0)
        #Log("(S)"+str(pl.somethingClose)+" "+str(pl.liftedUp) +" "+ str(pl.onCliff))
        
    #sleep(0.1)
    
    
    return not totalLostTmr.Expired()#if total lost timer expired, quit docking

def Log(s):
    print("LOGGED:"+str(s))

    dateStr=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open("logs/docking.log","a") as file:
        file.write(dateStr+" >> "+str(s)+"\n")

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
            Log("Keyboard interrupt, stopping!")
            break
    
    pl.Terminate()
    
    Log("END")

        

    
