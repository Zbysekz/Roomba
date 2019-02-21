#!/usr/bin/python3
from hardware.roombaPlatform import Platform
from features.docking import Dock
from features.wallFollowing import WallFollowing
from utils.stateMachine import StateMachine
from utils.timer import cTimer
import random
import RPi.GPIO as GPIO

pl  = 0 #platform
st  = 0 #state machine
st2 = 0 # state machine for cleaning

PIN_FAN = 16# fan in stack
PIN_SWEEPER = 21#sweeper
PIN_BRUSH = 20# main brush

GPIO.setmode(GPIO.BCM)
GPIO.setup(PIN_FAN, GPIO.OUT)
GPIO.setup(PIN_SWEEPER, GPIO.OUT)
GPIO.setup(PIN_BRUSH, GPIO.OUT)

tmr100ms = cTimer()
puls100ms = False
tmr5s = cTimer()
puls5s = False
#------------- timers for cleaning -----------------
spiralTmr = cTimer()
serverDataTmr = cTimer()

testTimer = cTimer()
cleaningTmr = cTimer()

#------------- auxilliary vars ---------------------
leftSpiral = False
bumpState = 0
storedState1=None
searchForBaseState=0
undockState=0
dockedCorrectlyTmr=0

def STATE_idle():
    if pl.isCharging:
        print("IS CHARGING!!!!!!")
        st.NextState(STATE_docked)
        testTimer.Start(20)
    else:
        st.NextState(STATE_searchForBase)
        
def STATE_docked():

    if st.getStepTime()>5:
        st.ResetStepTime()
        if not pl.isCharging:
            print("Not charging anymore")
            st.NextState(STATE_idle)
            
    if testTimer.Expired():
        print("GOING DO CLEANING")
        st.NextState(STATE_undock)
        cleaningTmr.Start(120)

def STATE_undock():
    global undockState
    
    if undockState==0:
        pl.Move(-50,-50,25)
        undockState=1
    elif undockState==1 and pl.standstill:
        pl.Rotate(Platform.LEFT,60,180)
        undockState=2
    elif undockState==2 and pl.standstill:
        st.NextState(STATE_cleaning)

def STATE_searchForBase():
    global searchForBaseState
    
    CheckLiftAndCliff()
    
    if searchForBaseState==0:
        speed = pl.getDynamicSpeed(30,100)
        pl.Move(speed,speed,ramp=20)
        
        if pl.bumper:
            searchForBaseState=1
            pl.Stop()
    elif searchForBaseState==1 and pl.standstill:
        pl.Move(-50,-50,10)
        searchForBaseState=2
    elif searchForBaseState==2 and pl.standstill:
        pl.RotateRandomDirAngle(speed=60)
        searchForBaseState=3
    elif searchForBaseState==3 and pl.standstill:
        searchForBaseState=0
    
    if pl.baseDetected:
        print("BASE detected! Docking!")
        st.NextState(STATE_docking)
    

def STATE_docking():
    global dockedCorrectlyTmr
    
    #CheckLiftAndCliff()
    dockingFail = Dock(pl)
    
    if pl.isCharging and puls100ms:
        dockedCorrectlyTmr+=1
    
    if not pl.isCharging:
        dockedCorrectlyTmr=0
    
    if dockedCorrectlyTmr>50:#5sec of charging means we are nicely docked
        st.NextState(STATE_docked)
        testTimer.Start(20)
    elif not dockingFail:#docking was unsuccesful, we lost base
        st.NextState(STATE_searchForBase)
    
    
def STATE_cleaning():
    
    CheckLiftAndCliff()

    #spiral at the start until you hit obstacle
    #then do wall following until time expires
    #bounce with random angle around the room for certain time
    #again do wall following
    #when time for cleaning is up, go search for base
    
    
    st2.Run()#run state machine for cleaning
    
    if pl.bumper and st2.currState != STATE_cleaning_bump:
        st2.NextState(STATE_cleaning_bump)
        
    if st2.currState == STATE_cleaning_spiral:
        if st2.getStepTime() > 30:
            st2.NextState(STATE_cleaning_wallFollowing)
            
    elif st2.currState == STATE_cleaning_wallFollowing:
        if st2.getStepTime() > 30:
            st2.NextState(STATE_cleaning_bouncing)
            
    elif st2.currState == STATE_cleaning_bouncing:
        if st2.getStepTime() > 30:
            st2.NextState(STATE_cleaning_spiral)
    
    if cleaningTmr.Expired():
        print("Time for cleaning expired!")
        st.NextState(STATE_searchForBase)
    
    
def STATE_cleaning_spiral():
    global leftSpiral,spiralValue
    
    if st2.First():
        leftSpiral = bool(random.randint(0,1))
        spiralValue=0
    
    if leftSpiral:
        pl.Move(int(spiralValue),60)
    else:
        pl.Move(60,int(spiralValue))
        
    if puls100ms:
        if spiralValue < 60:
            spiralValue += 0.3
    
def STATE_cleaning_wallFollowing():
    
    WallFollowing(pl)
    
def STATE_cleaning_bouncing():
    
    speed = pl.getDynamicSpeed(30,100)
    pl.Move(speed,speed,ramp=20)

def STATE_cleaning_bump():
    global bumpState
    if st2.First():
        bumpState=0
    #rotate and try go straight
    if pl.standstill and bumpState==0:
        pl.Move(-50,-50,10)
        bumpState=1
        
    if pl.standstill and bumpState==1:#we finished move back
        if pl.bumper:
            bumpState=0
        else:
            pl.Rotate(pl.LEFT,50,60)
            bumpState=2
        
    if bumpState==2 and pl.standstill:
        if pl.bumper:
            pl.Stop()
            bumpState=0
        else:
            pl.Move(20,20)
            bumpState=3
    
    if bumpState==3:
        if pl.bumper:
            pl.Stop()
            bumpState=0
        elif st2.getStepTime()>2: # we are moving at least 2 secs without bump
            st2.NextState(STATE_cleaning_bouncing)

def STATE_LiftOrCliff():
    
    pl.Stop()
    if puls5s:
        print("Lifted or on cliff!")
        
    if not pl.liftedUp and not pl.onCliff:
        st.NextState(storedState1)
    

def STATE_batteryLow():
    print("Battery low!")


def CheckLiftAndCliff(): # check if you are lifted or on the cliff
    global storedState1
    
    if pl.liftedUp or pl.onCliff:
        pl.Stop()
        storedState1 = st.currState
        st.NextState(STATE_LiftOrCliff)

def SendDataToServer():
    import socket

    host = "192.168.0.3"  
    port =  23     

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
     
    sock.connect((host, port))

    data = [7,102,int(pl.batVoltages[0]*1000/256),int(pl.batVoltages[0]*1000%256),\
            int(pl.batVoltages[1]*1000/256),int(pl.batVoltages[1]*1000%256),\
            int(pl.batVoltages[2]*1000/256),int(pl.batVoltages[2]*1000%256)]
    crc=0
    for d in data:
        crc+=d
    sent = sock.send(bytes([111,222]+data+[int(crc/256),crc%256,222]))
    
    print(data)
    print(bytes([111,222]+data+[int(crc/256),crc%256,222]))
    print("DATA SENT TO SERVER!!!")

    sock.close()

#----------------------------------------------------------------------------
def Cleaning():
    global st,pl,st2,tmr100ms,puls100ms,tmr5s,puls5s
    
    stateList = [
        STATE_idle,
        STATE_docked,
        STATE_searchForBase,
        STATE_docking,
        STATE_cleaning,
        STATE_batteryLow
    ]
    st = StateMachine(stateList)

    stateList2 = [
        STATE_cleaning_spiral,
        STATE_cleaning_wallFollowing,
        STATE_cleaning_bouncing
    ]
    st2 = StateMachine(stateList2)


    pl = Platform()

    pl.Connect()
    
    tmr100ms.Start(0.1)
    tmr5s.Start(5)
    
    while(1):
        try:
            pl.Preprocess()

            #main state machine
            st.Run()

            pl.RefreshTimeout()
            
            if tmr100ms.Expired():
                tmr100ms.Start(0.1)
                puls100ms=True
            else:
                puls100ms=False
                
            if tmr5s.Expired():
                tmr5s.Start(5)
                puls5s=True
            else:
                puls5s=False
                
            if serverDataTmr.Expired():
                serverDataTmr.Start(600)
                SendDataToServer()
                
        except KeyboardInterrupt:
            pl.Stop()
            print("Keyboard interrupt, stopping!")
            break
        
    pl.Terminate()
    
    print("END")



if __name__ == "__main__":

    Cleaning()
    

    
