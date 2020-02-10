#!/usr/bin/python
# -*- coding:utf-8 -*-
import RPi.GPIO as GPIO
import time
from multiprocessing import Process

ERROR = 0x00

PIN_L = 18#left sensor
PIN_R = 23#right sensor
PIN_T = 24#top sensor (force field)

#code defines
LEFT_BEAM = 0xA4
RIGHT_BEAM = 0xA8
FORCE_FIELD = 0xA1


GPIO.setmode(GPIO.BCM)
GPIO.setup(PIN_L, GPIO.IN, GPIO.PUD_UP)
GPIO.setup(PIN_R, GPIO.IN, GPIO.PUD_UP)
GPIO.setup(PIN_T, GPIO.IN, GPIO.PUD_OFF)

endThreads=False
startTime = 0
timeout = 35e-3

def getCode(pin):

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
 

def ReadL():
    while(not endThreads):
        code = getCode(PIN_L);
        if code != ERROR:
            print("L:0x%02x"%code)
        
        time.sleep(1)
#        lock.acquire()
#        if(code & LEFT_BEAM):
#            leftRateTmp[0]+=1
#        elif(code & RIGHT_BEAM):
#            leftRateTmp[1]+=1
#        elif(code & FORCE_FIELD):
#            leftRateTmp[2]+=1
#            
#        lock.release()
        
def ReadR():
    while(not endThreads):
        code = getCode(PIN_R);
        if code != ERROR:
            print("R:0x%02x"%code)
#        lock.acquire()
#        if(code & LEFT_BEAM):
#            rightRateTmp[0]+=1
#        elif(code & RIGHT_BEAM):
#            rightRateTmp[1]+=1
#        elif(code & FORCE_FIELD):
#            rightRateTmp[2]+=1
#            
#        lock.release()
        
def ReadT():
    global topRateTmp
    while(not endThreads):
        code = getCode(PIN_T);
        #if code != ERROR:
        print("T:0x%02x"%code)
     


if __name__ == "__main__":  
    print('IRM Start')
    
    while(True):
        code = getCode(PIN_L);
        if code != ERROR:
            print("L:0x%02x"%code)
            
        #time.sleep(1)
    
    #tL = Process(target=ReadL) #gute
    #tR = Process(target=ReadR) #gute
    #tT = Process(target=ReadT)
    #tL.start()
    #tR.start()
    #tT.start()
    #tS.start()
    
    input()
    print("TERMINATING")
    endThreads=True

        #else:
        #    print("ERROR")
#except KeyboardInterrupt:
 #   GPIO.cleanup();
