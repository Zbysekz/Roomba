#!/usr/bin/python
# -*- coding:utf-8 -*-
import RPi.GPIO as GPIO
import time
from multiprocessing import Process,Lock,Array
from operator import xor

from comm import *

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

leftRateTmp = [0,0,0]
rightRateTmp = [0,0,0]
topRateTmp = [0,0,0]


GPIO.setmode(GPIO.BCM)
GPIO.setup(PIN_L, GPIO.IN, GPIO.PUD_UP)
GPIO.setup(PIN_R, GPIO.IN, GPIO.PUD_UP)
GPIO.setup(PIN_T, GPIO.IN, GPIO.PUD_OFF)

endThreads=False

timeout = 35e-3

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
        
    
    #print(span)
    res = []
    
    for i in span:
        if(i>4.0e-3):
            res.append("TT")
        elif(i<2.0e-3):
            res.append("L")
        else:
            res.append("H")

    #print(res)
    
    if len(res)==16 and 'TT' not in res[:-1] and 'TT' == res[-1]:#if timeout character is only at the last index
        num=0
        y=0
        for i in range(8):
            if res[y]=='H' and (res[y+1]=='L' or i==7):# last one doesnt have L
                num+=(1<<7-i)
            y+=2
    
        return num
    
    return ERROR

def ReadL(lock,leftRateTmp):
    while(not endThreads):
        code = getCode(PIN_L);
        #if code != ERROR:
        #print("L:0x%02x"%code)
        lock.acquire()
        if(xor(code,LEFT_BEAM)==0):
            leftRateTmp[0]+=1
        if(xor(code,RIGHT_BEAM)==0):
            leftRateTmp[1]+=1
        if(xor(code,FORCE_FIELD)==0):
            leftRateTmp[2]+=1
            
        lock.release()
        
def ReadR(lock,rightRateTmp):
    while(not endThreads):
        code = getCode(PIN_R);
        #if code != ERROR:
        #print("R:0x%02x"%code)
        lock.acquire()
        if(xor(code,LEFT_BEAM)==0):
            rightRateTmp[0]+=1
        if(xor(code,RIGHT_BEAM)==0):
            rightRateTmp[1]+=1
        if(xor(code,FORCE_FIELD)==0):
            rightRateTmp[2]+=1
            
        lock.release()
        
def ReadT(lock,topRateTmp):
    while(not endThreads):
        code = getCode(PIN_T);
        #if code != ERROR:
        #print("T:0x%02x"%code)
        lock.acquire()
        
        if(xor(code,LEFT_BEAM)==0):
            topRateTmp[0]+=1
        if(xor(code,RIGHT_BEAM)==0):
            topRateTmp[1]+=1
        if(xor(code,FORCE_FIELD)==0):
            topRateTmp[2]+=1
        
        lock.release()

def RateSampler(lock,leftRateTmp,rightRateTmp,topRateTmp):
    global leftRate,rightRate,topRate
    
    while(not endThreads):
        lock.acquire()
        
        leftRate=[leftRateTmp[0],leftRateTmp[1],leftRateTmp[2]]
        rightRate=[rightRateTmp[0],rightRateTmp[1],rightRateTmp[2]]
        topRate=[topRateTmp[0],topRateTmp[1],topRateTmp[2]]
        
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
        
        
        print("L:"+str(leftRate[0])+","+str(leftRate[1])+","+str(leftRate[2]))
        print("R:"+str(rightRate[0])+","+str(rightRate[1])+","+str(rightRate[2]))
        print("T:"+str(topRate[0])+","+str(topRate[1])+","+str(topRate[2]))
    
        if(leftRate[0]+leftRate[1] > rightRate[0]+rightRate[1]):
            Move(0,20)
        elif(leftRate[0]+leftRate[1] < rightRate[0]+rightRate[1]):
            Move(20,0)
        elif(topRate[2]>0):
            Move(5,5)
        else:
            Move(0,0)
        
        time.sleep(0.5)

if __name__ == "__main__":  
    print('IRM Start')
    
    Init();
    
    Move(0,0)
    
    leftRateTmp = Array('i',range(3))
    rightRateTmp = Array('i',range(3))
    topRateTmp = Array('i',range(3))

    lock = Lock()
    tS = Process(target=RateSampler,args=(lock,leftRateTmp,rightRateTmp,topRateTmp))
    
    tL = Process(target=ReadL,args=(lock,leftRateTmp)) #gute
    tR = Process(target=ReadR,args=(lock,rightRateTmp)) #gute
    tT = Process(target=ReadT,args=(lock,topRateTmp))
    tL.start()
    tR.start()
    tT.start()
    tS.start()
    
    input()
    print("TERMINATING")
    tL.terminate()
    tR.terminate()
    tS.terminate()
    tT.terminate()

        #else:
        #    print("ERROR")
#except KeyboardInterrupt:
 #   GPIO.cleanup();