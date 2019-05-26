#!/usr/bin/python3
from hardware.roombaPlatform import Platform
from features.docking import Dock
from features.wallFollowing import WallFollowing
from utils.stateMachine import StateMachine
from utils.timer import cTimer
import random

import os,inspect
path = os.path.dirname(inspect.getfile(inspect.currentframe()))
os.chdir(path)#change CWD to this file location, to keep required folders and files reachable

import time 
from time import sleep
import calendar
from datetime import date,datetime

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
restCleaningTmr = cTimer()

#------------- auxilliary vars ---------------------
leftSpiral = False
bumpState = 0
storedState1=None
storedState2=None
searchForBaseState=0
undockState=0
cliffState=0
dockedCorrectlyTmr=0
storedCleaningMotors=False#if roomba was cleaning before lifted or cliff
permaDir=None


testCleaning=False


def STATE_idle():
    
    # determine where you are
    if pl.isCharging:
        Log("Started up at docking station")
        st.NextState(STATE_docked)
        testTimer.Start(10)
    else:
        if testCleaning:
            Log("GOING DO TEST CLEANING!")
            pl.StartCleaningMotors()
            st.NextState(STATE_cleaning)
            cleaningTmr.Start(600)#10min
        elif pl.liftedUp or pl.onCliff:
            Log("Lifted! Waiting..")
            st.NextState(STATE_manualStop)#somebody lifted me(probably from dock), wait
        else:        
            Log("Started outside docking station, going to dock!")
            st.NextState(STATE_searchForBase)
        
def STATE_docked():

    if st.First():
        pl.StopCleaningMotors();
        restCleaningTmr.Start(20)#for testing cleaning dock break
        
    if st.getStepTime()>5:
        st.ResetStepTime()
        if not pl.isCharging:
            Log("Not charging anymore")
            st.NextState(STATE_idle)
            
    if CheckCleaningSchedule():
        Log("GOING DO SCHEDULED CLEANING!")
        st.NextState(STATE_undock)
        cleaningTmr.Start(600)#10min
        
    if testCleaning and restCleaningTmr.Expired():
        Log("GOING DO TEST CLEANING!")
        st.NextState(STATE_undock)
        cleaningTmr.Start(600)#10min

def STATE_undock():
    global undockState
    
    if st.First():
        undockState = 0
    
    if undockState==0:#go back
        pl.Move(-50,-50,25)
        undockState=1
    elif undockState==1 and pl.standstill:#rotate to left
        pl.Rotate(Platform.LEFT,60,180)
        undockState=2
    elif undockState==2 and pl.standstill:#start cleaning motors
        pl.StartCleaningMotors()
        st.NextState(STATE_cleaning)
        
    
    sleep(0.1)

def STATE_searchForBase():
    global searchForBaseState,permaDir
    
    if st.First():
        permaDir = Platform.LEFT if bool(random.randint(0,1))else Platform.RIGHT
    
    CheckLiftAndCliff()
    
    if searchForBaseState==0:
        speed = pl.getDynamicSpeed(30,70)
        pl.Move(speed,speed,ramp=20)
        
        if pl.bumper:
            searchForBaseState=1
            pl.Stop()
    elif searchForBaseState==1 and pl.standstill:
        pl.Move(-50,-50,5)
        searchForBaseState=2
    elif searchForBaseState==2 and pl.standstill:
        pl.RotateRandomAngle(direction=permaDir,speed=60,angleMin=15,angleMax=60)
        searchForBaseState=3
    elif searchForBaseState==3 and pl.standstill:
        searchForBaseState=0
    
    if pl.baseDetected:
        Log("BASE detected! Docking!")
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
            
    elif st2.currState == STATE_cleaning_bouncing:#if you are bouncing and some time elapsed and you traveled some distance without bump, go spiral
        if st2.getAcumulatedTime() > 30 and pl.straightDistanceTraveled>100:
            st2.ResetAcumulatedTime()
            st2.NextState(STATE_cleaning_spiral)
            
    #avoid going too close to base
    if pl.getTopRate()[Platform.TOP]>4 and st2.currState != STATE_cleaning_baseClose:
        Log("Base is close,going out of here")
        st2.NextState(STATE_cleaning_baseClose)
    
    if pl.lowBattery:
        Log("Low battery! Going to base!")
        pl.StopCleaningMotors()
        st.NextState(STATE_searchForBase)
    
    if cleaningTmr.Expired():
        Log("Time for cleaning expired!")
        #pl.StopCleaningMotors()
        st.NextState(STATE_searchForBase)
    
def STATE_cleaning_baseClose():
    if st2.First():
        pl.RotateRandomAngle(Platform.LEFT if bool(random.randint(0,1))else Platform.RIGHT,60,30,180)#rotate to random dir by random angle
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
            
    #sleep(0.1)
    
def STATE_cleaning_wallFollowing():
    
    WallFollowing(pl)
    
def STATE_cleaning_bouncing():
    
    speed = pl.getDynamicSpeed(25,50)
    pl.Move(speed,speed,ramp=20)
    
    
    #sleep(0.1)

def STATE_cleaning_bump():
    global bumpState
    
    if st2.First():
        bumpState=0
   
    if pl.standstill and bumpState==0:#after bump go back
        pl.Move(-100,-100,5)
        bumpState=1
        
    if pl.standstill and bumpState==1:#finished move back,rotate
        if pl.bumper:
            bumpState=0
        else:
            pl.Rotate(pl.LEFT,50,20)
            bumpState=2
        
    if bumpState==2 and pl.standstill:#finished rotation, go front
        if pl.bumper:
            pl.Stop()
            bumpState=0
        else:
            pl.Move(40,40)
            bumpState=3
    
    if bumpState==3:
        if pl.bumper:
            pl.Stop()
            bumpState=0
        elif st2.getStepTime()>2: # we are moving at least 2 secs without bump
            st2.NextState(storedState2)


    #sleep(0.1)

def STATE_LiftOrCliff():
    global cliffState
    
    if st.First():
        Log("Lifted or on cliff!")
        Log("SensorData:"+str(pl.sensorData[1]))
        
        if pl.onCliff and not pl.liftedUp:#if just on cliff,move backwards
            pl.Move(-40,-40,50)
            
        cliffState = 0
    
    if pl.liftedUp:
        pl.StopCleaningMotors()
        
      
    elif pl.standstill and not pl.liftedUp and cliffState==0:
        cliffState=1
        pl.Rotate(Platform.LEFT,60,60)
    
    elif pl.standstill and not pl.liftedUp and not pl.onCliff and cliffState==1:
        st.NextState(storedState1)
        if storedCleaningMotors:
            pl.StartCleaningMotors()
      
    #timeout
    if st.getStepTime()>15:
        Log("Timeout in LiftOrCLiff state! Turning off everything...")
        pl.Stop()
        pl.StopCleaningMotors()
        st.NextState(STATE_stuck)
        

def STATE_batteryVeryLow():
    #wait if somebody has put me to the docking station
    if(st.getStepTime()>=30):
        if pl.isCharging:
            Log("On very low battery,but now on docking station!")
            st.NextState(STATE_docked)
        else:
            os.system('Shutdown.sh')#shutdown RPi and BMS
            

def STATE_motorsOverloaded():
    sleep(5)
    
def STATE_cleaningMotorsOverloaded():
    sleep(5)
    
def STATE_stuck():
    sleep(5)
    
def STATE_manualStop():
    if pl.isCharging:
        Log("Manually docked to station")
        st.NextState(STATE_docked)
    
def CheckLiftAndCliff(): # check if you are lifted or on the cliff
    global storedState1,storedCleaningMotors
    
    if pl.liftedUp or pl.onCliff:
        Log("Lifted up or on Clif!!")
        pl.Stop()
        storedCleaningMotors = pl.getCleaningMotorsState()
        if pl.liftedUp:#stop cleaning only if lifted up
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
    
    Log(data)
    Log(bytes([111,222]+data+[int(crc/256),crc%256,222]))
    Log("DATA SENT TO SERVER!!!")

    sock.close()

#----------------------------------------------------------------------------
def Cleaning():
    global st,pl,st2,tmr100ms,puls100ms,tmr5s,puls5s,storedState1
    
    Log("-------------------CLEANING SCRIPT STARTED--------------------------")
    
    stateList = [
        STATE_idle,
        STATE_docked,
        STATE_searchForBase,
        STATE_undock,
        STATE_docking,
        STATE_cleaning,
        STATE_batteryVeryLow,
        STATE_LiftOrCliff,
        STATE_motorsOverloaded,
        STATE_cleaningMotorsOverloaded,
        STATE_stuck,
        STATE_manualStop
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
    
    current_milis_time = lambda: int(round(time.time() * 1000))
    
    
    #---------------------------self check--------------------------
    while(not pl.validData):
        Log("Waiting for first valid data from Motherboard...")
        pl.Preprocess()
        sleep(1)
    
    pl.Preprocess()
    
    sleep(3)#wait to stabilize zero current
    if not pl.cleaningMotorsCurrentStandstill:
        Log("Current of cleaning motors is not zero! Possible fault connection!")
        Log("Current:"+str(pl.cleaningMotorsCurrent))
        while(True):
            pl.Preprocess()
            Log("Current:"+str(pl.cleaningMotorsCurrent))
            sleep(1)
            pass
    
    #------------------------- end self check------------------------
    
    last_dt = current_milis_time()
    
    while(1):
        try:
            #dt = current_milis_time()-last_dt
            #print("DT:"+str(dt))
            #last_dt = current_milis_time()
            
            pl.Preprocess()

            #main state machine
            st.Run()

            pl.RefreshTimeout()
            
            if not pl.isCharging and pl.veryLowBattery and st.currState != STATE_batteryVeryLow:
                Log("Battery very low!")
                Log(pl.batVoltages)
                pl.Stop()
                pl.StopCleaningMotors()
                st.NextState(STATE_batteryVeryLow)
            
            if pl.motorsOverloaded and st.currState != STATE_motorsOverloaded:
                Log("Motors overloaded!")
                pl.Stop()
                pl.StopCleaningMotors()
                storedState1 = st.currState
                st.NextState(STATE_motorsOverloaded)
                
            if pl.cleaningMotorsOverloaded and st.currState != STATE_cleaningMotorsOverloaded:
                Log("Cleaning motors overloaded!")
                Log("Current:"+str(pl.cleaningMotorsCurrent))
                pl.Stop()
                pl.StopCleaningMotors()
                storedState1 = st.currState
                st.NextState(STATE_cleaningMotorsOverloaded)
             
             
             # buttons ------------------------------------------
            if pl.btn1 and st.currState!=STATE_manualStop:
                Log("MANUAL STOP!")
                pl.Stop()
                pl.StopCleaningMotors()
                st.NextState(STATE_manualStop)
            
            if pl.btn2 and st.currState!=STATE_undock:
                Log("GOING DO MANUALLY STARTED CLEANING!")
                if pl.isCharging:
                    st.NextState(STATE_undock)
                else:
                    pl.StartCleaningMotors()
                    st.NextState(STATE_cleaning)
        
                cleaningTmr.Start(600)#10min
                
            if pl.btn3 and st.currState!=STATE_searchForBase:
                Log("GOING DO MANUALLY STARTED DOCKING!")
                st.NextState(STATE_searchForBase)
              
            # buttons ------------------------------------------
            
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
                pl.PrintErrorCnt()
                
        except KeyboardInterrupt:
            pl.Stop()
            pl.StopCleaningMotors()
            Log("------------Keyboard interrupt, stopping!---------------")
            break
        
    pl.Terminate()
    
    Log("END")


def CheckCleaningSchedule():
    
    myDate = date.today()
    thisDay = calendar.day_name[myDate.weekday()]
    
    thisHour = datetime.now().time().hour
    thisMinute = datetime.now().time().minute
    
    lst = []
    
    with open("cleaningSchedule.txt","r") as f:
        for l in f:
            s = l.split(',')
            s[1:] = s[1].split(':')
            s[1] = int(s[1])
            s[2] = int(s[2])
            lst.append(s)
            
    
    
    for l in lst:
        if thisDay == l[0] and thisHour == l[1] and thisMinute == l[2]:
            Log("Scheduled! Lets go cleaning!")
            return True
    return False

def Log(s):
    print("LOGGED:"+str(s))

    dateStr=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    with open("logs/cleaning.log","a") as file:
        file.write(dateStr+" >> "+str(s)+"\n")

if __name__ == "__main__":

    Cleaning()
    

    
