#!/usr/bin/python3
from hardware.roombaPlatform import Platform
from features.docking import Dock
from features.wallFollowing import WallFollowing
from utils.stateMachine import StateMachine
from utils.timer import cTimer
import random

from time import sleep

pl  = 0 #platform
st  = 0 #state machine
st2 = 0 # state machine for cleaning


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
storedState2=None
searchForBaseState=0
undockState=0
dockedCorrectlyTmr=0
storedCleaningMotors=False#if roomba was cleaning before lifted or cliff
testCleaning=True

def STATE_idle():
    if pl.isCharging:
        print("IS CHARGING!!!!!!")
        st.NextState(STATE_docked)
        testTimer.Start(10)
    else:
        st.NextState(STATE_searchForBase)
        
def STATE_docked():

    if st.getStepTime()>5:
        st.ResetStepTime()
        if not pl.isCharging:
            print("Not charging anymore")
            st.NextState(STATE_idle)
            
    if testTimer.Expired() and testCleaning:
        print("GOING DO CLEANING")
        st.NextState(STATE_undock)
        cleaningTmr.Start(300)

def STATE_undock():
    global undockState
    
    if undockState==0:
        pl.Move(-50,-50,25)
        undockState=1
    elif undockState==1 and pl.standstill:
        pl.Rotate(Platform.LEFT,60,180)
        undockState=2
    elif undockState==2 and pl.standstill:
        pl.StartCleaningMotors()
        st.NextState(STATE_cleaning)
        
    
    sleep(0.1)

def STATE_searchForBase():
    global searchForBaseState
    
    CheckLiftAndCliff()
    
    if searchForBaseState==0:
        speed = pl.getDynamicSpeed(30,70)
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
        
    
    sleep(0.1)   

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
    global storedState2
    
    CheckLiftAndCliff()

    #spiral at the start until you hit obstacle
    #then do wall following until time expires
    #bounce with random angle around the room for certain time
    #again do wall following
    #when time for cleaning is up, go search for base
    
    
    st2.Run()#run state machine for cleaning
    
    if pl.bumper and st2.currState != STATE_cleaning_bump:
        storedState2=st2.currState
        st2.NextState(STATE_cleaning_bump)
        
    if st2.currState == STATE_cleaning_spiral:
        if st2.getAcumulatedTime() > 30:
            st2.ResetAcumulatedTime()
            st2.NextState(STATE_cleaning_wallFollowing)
            
    elif st2.currState == STATE_cleaning_wallFollowing:
        if st2.getAcumulatedTime() > 30:
            st2.ResetAcumulatedTime()
            st2.NextState(STATE_cleaning_bouncing)
            
    elif st2.currState == STATE_cleaning_bouncing:
        if st2.getAcumulatedTime() > 30:
            st2.ResetAcumulatedTime()
            st2.NextState(STATE_cleaning_spiral)
            
    #avoid going too close to base
    if pl.getTopRate()[Platform.TOP]>4 and st2.currState != STATE_cleaning_baseClose:
        print("Base is close,going out of here")
        st2.NextState(STATE_cleaning_baseClose)
    
    if pl.lowBattery:
        print("Low battery! Going to base!")
        pl.StopCleaningMotors()
        st.NextState(STATE_searchForBase)
    
    if cleaningTmr.Expired():
        print("Time for cleaning expired!")
        pl.StopCleaningMotors()
        st.NextState(STATE_searchForBase)
    
def STATE_cleaning_baseClose():
    if st2.First():
        pl.RotateRandomDirAngle(60,30,180)
    elif pl.standstill:
        st2.NextState(STATE_cleaning_bouncing)
        
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
            
    sleep(0.1)
    
def STATE_cleaning_wallFollowing():
    
    WallFollowing(pl)
    
def STATE_cleaning_bouncing():
    
    speed = pl.getDynamicSpeed(25,50)
    pl.Move(speed,speed,ramp=20)
    
    
    sleep(0.1)

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
            st2.NextState(storedState2)


    sleep(0.1)

def STATE_LiftOrCliff():
    
    pl.Stop()
    if puls5s:
        print("Lifted or on cliff!")
        
    if not pl.liftedUp and not pl.onCliff:
        st.NextState(storedState1)
        if storedCleaningMotors:
            pl.StartCleaningMotors()
    

def STATE_batteryVeryLow():
    print("Battery very low!")


def CheckLiftAndCliff(): # check if you are lifted or on the cliff
    global storedState1,storedCleaningMotors
    
    if pl.liftedUp or pl.onCliff:
        pl.Stop()
        storedCleaningMotors = pl.getCleaningMotorsState()
        pl.StopCleaningMotors()
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
        STATE_undock,
        STATE_docking,
        STATE_cleaning,
        STATE_batteryVeryLow,
        STATE_LiftOrCliff
    ]
    st = StateMachine(stateList)

    stateList2 = [
        STATE_cleaning_bouncing,
        STATE_cleaning_spiral,
        STATE_cleaning_wallFollowing,
        STATE_cleaning_bump,
        STATE_cleaning_baseClose
    ]
    st2 = StateMachine(stateList2)


    pl = Platform()

    pl.Connect()
    
    tmr100ms.Start(0.1)
    tmr5s.Start(5)
    serverDataTmr.Start(1)
    
    while(1):
        try:
            pl.Preprocess()

            #main state machine
            st.Run()

            pl.RefreshTimeout()
            
            if pl.veryLowBattery and st.currState != STATE_batteryVeryLow:
                st.NextState(STATE_batteryVeryLow)
            
            if tmr100ms.Expired():
                tmr100ms.Start(0.1)
                puls100ms=True
            else:
                puls100ms=False
                
            if tmr5s.Expired():
                tmr5s.Start(5)
                puls5s=True
                pl.PrintErrorCnt()
            else:
                puls5s=False
                
            if serverDataTmr.Expired():
                serverDataTmr.Start(600)
                SendDataToServer()
                
        except KeyboardInterrupt:
            pl.Stop()
            pl.StopCleaningMotors()
            print("Keyboard interrupt, stopping!")
            break
        
    pl.Terminate()
    
    print("END")



if __name__ == "__main__":

    Cleaning()
    

    
