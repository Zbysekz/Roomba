#!/usr/bin/python
# -*- coding:utf-8 -*-
import RPi.GPIO as GPIO
import time
import multiprocessing

ERROR = 0xFE
PIN_L = 18#left sensor
PIN_R = 23#right sensor
PIN_T = 24#top sensor (force field)

GPIO.setmode(GPIO.BCM)
GPIO.setup(PIN_L, GPIO.IN, GPIO.PUD_UP)
GPIO.setup(PIN_R, GPIO.IN, GPIO.PUD_UP)
GPIO.setup(PIN_T, GPIO.IN, GPIO.PUD_OFF)

endThreads=False

def getCode(pin):
    byte = [0, 0, 0, 0];
    
    if IRStart(pin) == False:
        time.sleep(0.035);        # One message frame lasts 32 ms.
        #print("ERR2")
        return ERROR;
    else:
        
        
        timeSpan = [];
        timeSpan.append(Measure(pin,GPIO.RISING));
        
            
        for i in range(0,6):
            
            timeSpan.append(Measure(pin,GPIO.FALLING));
            timeSpan.append(Measure(pin,GPIO.RISING));
        
        #print(len(timeSpan))
        #print(timeSpan)
        
        bits = [1]#starting bit is one
        
        for i in range(0,12,2):
            if(timeSpan[i] + timeSpan[i+1] >3.2e-3 and timeSpan[i] + timeSpan[i+1] <4e-3):
                if timeSpan[i] < timeSpan[i+1]:
                    bits.append(0)
                else:
                    bits.append(1)
            else:
                #print("ERR1")
                return ERROR
        if timeSpan[-1]>1.5e-3:
            bits.append(1)
        else:
            bits.append(0)
              
        res=0
        ll=len(bits)
        for i in range(ll):
            res+=bits[ll-i-1]<<i
        #print(res)
        
        return res

def Measure(pin,edge):
    timeBuf = time.time();
    span=0
    while(span<0.6e-3):
        GPIO.wait_for_edge(pin, edge,timeout=4);
        span = time.time() - timeBuf
    
    return span
    
def IRStart(pin):
    timeFallingEdge = [0, 0];
    timeRisingEdge = 0;
    timeSpan = [0, 0];
    GPIO.wait_for_edge(pin, GPIO.FALLING);
    timeFallingEdge[0] = time.time();
    GPIO.wait_for_edge(pin, GPIO.RISING,timeout=4);
    timeRisingEdge = time.time();
    GPIO.wait_for_edge(pin, GPIO.FALLING,timeout=4);
    timeFallingEdge[1] = time.time();
    timeSpan[0] = timeRisingEdge - timeFallingEdge[0];
    timeSpan[1] = timeFallingEdge[1] - timeRisingEdge;
    # Start signal is composed with a 9 ms leading space and a 4.5 ms pulse.
    #print(timeSpan)
    if timeSpan[0] > 2.8e-3 and \
       timeSpan[0] < 3.2e-3 and \
       timeSpan[1] > 0.6e-3 and \
       timeSpan[1] < 1.2e-3:
        return True;
    else:
        #print(timeSpan)
        return False;

def ReadL():
    while(not endThreads):
        code = getCode(PIN_L);
        print("L:0x%02x"%code)
def ReadR():
    while(not endThreads):
        code = getCode(PIN_R);
        print("R:0x%02x"%code)
def ReadT():
    while(not endThreads):
        code = getCode(PIN_T);
        print("T:0x%02x"%code)
        

if __name__ == "__main__":  
    print('IRM Start')

    tL = multiprocessing.Process(target=ReadL)
    tR = multiprocessing.Process(target=ReadR)
    tT = multiprocessing.Process(target=ReadT)
    tL.start()
    tR.start()
    tT.start()
    
    input()
    print("TERMINATING")
    endThreads=True

        #else:
        #    print("ERROR")
#except KeyboardInterrupt:
 #   GPIO.cleanup();