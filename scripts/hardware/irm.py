#!/usr/bin/python
# -*- coding:utf-8 -*-
import RPi.GPIO as GPIO
import time
from datetime import datetime
from multiprocessing import Process,Lock,Value,Array

ERROR = 0x00

PIN_L = 23#left sensor
PIN_R = 18#right sensor
PIN_T = 24#top sensor (force field)

#code defines
LEFT_BEAM = 0xA8
RIGHT_BEAM = 0xA4
FORCE_FIELD = 0xA1

leftRate = [0,0,0]
rightRate = [0,0,0]
topRate = [0,0,0]


GPIO.setmode(GPIO.BCM)
GPIO.setup(PIN_L, GPIO.IN, GPIO.PUD_UP)
GPIO.setup(PIN_R, GPIO.IN, GPIO.PUD_UP)
GPIO.setup(PIN_T, GPIO.IN, GPIO.PUD_OFF)

endThreads=False
printInfo=False
timeout = 35e-3

tL=0
tR=0
tS=0
tT=0

def getCode(pin):
    startTime = 0
    span=[]
        
    GPIO.wait_for_edge(pin, GPIO.FALLING);
    startTime = time.time()
    
    GPIO.wait_for_edge(pin, GPIO.RISING,timeout=4);
    
    t=time.time()
    span.append(t-startTime)
    
    while(len(span)<16):
        GPIO.wait_for_edge(pin, GPIO.FALLING,timeout=4);
        span.append(time.time()-t)
        t = time.time()
        
        if(t-startTime>timeout or not len(span)<16):
            break
        
        GPIO.wait_for_edge(pin, GPIO.RISING,timeout=4);
        span.append(time.time()-t)
        t = time.time()
        
        if(t-startTime>timeout):
            break
        
    
    #Log(span)
    res = []
    
    for i in span:
        if(i>4.0e-3):
            res.append("TT")
        elif(i<2.0e-3):
            res.append("L")
        else:
            res.append("H")

    #if pin == PIN_R:
        #Log(res)
    
    if len(res)==16 and 'TT' not in res[:-1] and 'TT' == res[-1]:#if timeout character is only at the last index
        num=0
        y=0
        for i in range(8):
            if res[y]=='H' and (res[y+1]=='L' or i==7):# last one doesnt have L
                num+=(1<<7-i)
            y+=2
    
        return num
    
    return ERROR

def ReadL(lock,tmrTimeout,leftRateTmp):
    try:
        while(not endThreads and tmrTimeout.value!=0):

            code = getCode(PIN_L);
            #if code != ERROR:
            #Log("L:0x%02x"%code)
            lock.acquire()
            tmrTimeout.value-=1

            if((code & LEFT_BEAM)==LEFT_BEAM):
                leftRateTmp[0]+=1
            if((code & RIGHT_BEAM)==RIGHT_BEAM):
                leftRateTmp[1]+=1
            if((code & FORCE_FIELD)==FORCE_FIELD):
                leftRateTmp[2]+=1

            lock.release()
    except KeyboardInterrupt:
        Log("------------IRM Read L - Keyboard interrupt!---------------")

    Log("tL process terminated")
        
def ReadR(lock,tmrTimeout,rightRateTmp):
    try:
        while(not endThreads and tmrTimeout.value!=0):

            code = getCode(PIN_R);
            #if code != ERROR:
            #Log("R:0x%02x"%code)
            lock.acquire()
            tmrTimeout.value-=1

            if((code & LEFT_BEAM)==LEFT_BEAM):
                rightRateTmp[0]+=1
            if((code & RIGHT_BEAM)==RIGHT_BEAM):
                rightRateTmp[1]+=1
            if((code & FORCE_FIELD)==FORCE_FIELD):
                rightRateTmp[2]+=1

            lock.release()
    except KeyboardInterrupt:
        Log("------------IRM Read R - Keyboard interrupt!---------------")

    Log("tR process terminated")
        
def ReadT(lock,tmrTimeout,topRateTmp):
    try:
        while(not endThreads and tmrTimeout.value!=0):

            code = getCode(PIN_T);
            #if code != ERROR:
            #Log("T:0x%02x"%code)
            lock.acquire()
            tmrTimeout.value-=1

            if((code & LEFT_BEAM)==LEFT_BEAM):
                topRateTmp[0]+=1
            if((code & RIGHT_BEAM)==RIGHT_BEAM):
                topRateTmp[1]+=1
            if((code & FORCE_FIELD)==FORCE_FIELD):
                topRateTmp[2]+=1

            lock.release()
    except KeyboardInterrupt:
        Log("------------IRM Read T - Keyboard interrupt!---------------")

    Log("tT process terminated")

def RateSampler(lock,tmrTimeout,leftRate,rightRate,topRate,leftRateTmp,rightRateTmp,topRateTmp,prInfo):
    try:
        while(not endThreads and tmrTimeout.value!=0):

            lock.acquire()
            tmrTimeout.value-=1

            leftRate[0]=leftRateTmp[0]
            leftRate[1]=leftRateTmp[1]
            leftRate[2]=leftRateTmp[2]

            rightRate[0]=rightRateTmp[0]
            rightRate[1]=rightRateTmp[1]
            rightRate[2]=rightRateTmp[2]

            topRate[0]=topRateTmp[0]
            topRate[1]=topRateTmp[1]
            topRate[2]=topRateTmp[2]

            leftRateTmp[0]=0
            leftRateTmp[1]=0
            leftRateTmp[2]=0
            rightRateTmp[0]=0
            rightRateTmp[1]=0
            rightRateTmp[2]=0
            topRateTmp[0]=0
            topRateTmp[1]=0
            topRateTmp[2]=0


            lock.release()


            if prInfo:
                Log("L:"+str(leftRate[0])+","+str(leftRate[1])+","+str(leftRate[2]))
                Log("R:"+str(rightRate[0])+","+str(rightRate[1])+","+str(rightRate[2]))
                Log("T:"+str(topRate[0])+","+str(topRate[1])+","+str(topRate[2]))

            time.sleep(0.5)
    except KeyboardInterrupt:
        Log("------------IRM Rate sampler - Keyboard interrupt!---------------")

    Log("tS process terminated")

def getLeftRate():
    return [leftRate[0],leftRate[1],leftRate[2]]
def getRightRate():
    return [rightRate[0],rightRate[1],rightRate[2]]
def getTopRate():
    return [topRate[0],topRate[1],topRate[2]]

def Start():
    global tL,tR,tT,tS,tmrTimeout,leftRate,rightRate,topRate,printInfo
    
    leftRate = Array('i',range(3))
    rightRate = Array('i',range(3))
    topRate = Array('i',range(3))
    
    leftRateTmp = Array('i',range(3))
    rightRateTmp = Array('i',range(3))
    topRateTmp = Array('i',range(3))
    
    leftRateTmp[0]=0
    leftRateTmp[1]=0
    leftRateTmp[2]=0
    rightRateTmp[0]=0
    rightRateTmp[1]=0
    rightRateTmp[2]=0
    topRateTmp[0]=0
    topRateTmp[1]=0
    topRateTmp[2]=0
    
    tmrTimeout = Value('i',300)

    lock = Lock()
    tS = Process(target=RateSampler,args=(lock,tmrTimeout,leftRate,rightRate,topRate,leftRateTmp,rightRateTmp,topRateTmp,printInfo))
    
    tL = Process(target=ReadL,args=(lock,tmrTimeout,leftRateTmp)) #gute
    tR = Process(target=ReadR,args=(lock,tmrTimeout,rightRateTmp)) #gute
    tT = Process(target=ReadT,args=(lock,tmrTimeout,topRateTmp))
    tL.start()
    tR.start()
    tT.start()
    tS.start()

def Terminate():
    tL.terminate()
    tR.terminate()
    tS.terminate()
    tT.terminate()
    
def Log(s):
    print("LOGGED:"+str(s))

    dateStr=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open("logs/irm.log","a") as file:
        file.write(dateStr+" >> "+str(s)+"\n")

    
if __name__ == "__main__":  
    Log('IRM Start')
    
    printInfo = True
    Start()
    
    try:
        while(True):
            tmrTimeout.value=300
            time.sleep(5)
    except KeyboardInterrupt:
        Log("Keyboard interrupt, stopping!")
    
    Log("TERMINATING")
    Terminate()

        #else:
        #    Log("ERROR")
#except KeyboardInterrupt:
 #   GPIO.cleanup();