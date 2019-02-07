#!/usr/bin/python3
from hardware.roombaPlatform import Platform
from features.docking import Dock
from utils.stateMachine import StateMachine
from utils.timer import cTimer
import random

pl  = 0 #platform
st  = 0 #state machine
st2 = 0 # state machine for cleaning

tmr100ms = cTimer()
puls100ms = False
tmr5s = cTimer()
puls5s = False
#------------- timers for cleaning -----------------
spiralTmr = cTimer()

#------------- auxilliary vars ---------------------
leftSpiral = False
bumpState = 0
storedState1=None


def STATE_idle():
    if pl.isCharging:
        st.NextState(STATE_docked)
    else:
        st.NextState(STATE_docking)
        
def STATE_docked():

    if st.getStepTime()>5:
        st.ResetStepTime()
        if not pl.isCharging:
            print("Not charging anymore")
            st.NextState(STATE_idle)

def STATE_searchForBase():
    
    CheckLiftAndCliff()
    print("searchForBase")    

def STATE_docking():
    CheckLiftAndCliff()
    Dock(pl)
    
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
    
    if st2.getStepTime() > 10:
        st2.NextState(STATE_cleaning_wallFollowing)
    
def STATE_cleaning_wallFollowing():
    
    pl.Move(0,0)
    
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
        elif st2.getStepTime()>2: # we are moving at least 2 secs withotu bump
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
                
        except KeyboardInterrupt:
            pl.Stop()
            print("Keyboard interrupt, stopping!")
            break
        
    pl.Terminate()
    
    print("END")



if __name__ == "__main__":

    Cleaning()
    

    
