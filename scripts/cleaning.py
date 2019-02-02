#!/usr/bin/python3
from hardware.roombaPlatform import Platform
from features.docking import Dock
from stateMachine import StateMachine

st = 0 #state machine
pl = 0 #platform

def STATE_idle():
    if pl.isCharging:
        st.NextState(STATE_docked)
        
def STATE_docked():

    if st.CheckTimeout(5):
        st.ResetTimeout()
        if not st.isCharging:
            print("Not charging anymore")
            st.NextState(STATE_idle)

def STATE_searchForBase():
    print("")    

def STATE_docking():
    Dock()
    
def STATE_cleaning():

    #spiral at the start until you hit obstacle
    #then do wall following until time expires
    #bounce with random angle around the room for certain time
    #again do wall following
    #when time for cleaning is up, go search for base
    print("")
def STATE_batteryLow():
    print("")

#----------------------------------------------------------------------------
def Cleaning():
    global st,pl
    
    stateList = [
        STATE_idle,
        STATE_docked,
        STATE_searchForBase,
        STATE_docking,
        STATE_cleaning,
        STATE_batteryLow
    ]
    st = StateMachine(stateList)

    pl = Platform()

    pl.Connect()
    
    while(1):
        try:
            pl.Preprocess()

            #main state machine
            st.Run()

            pl.RefreshTimeout()
        except KeyboardInterrupt:
            pl.Move(0,0)
            print("Keyboard interrupt, stopping!")
        
    pl.Terminate()
    
    print("END")



if __name__ == "__main__":

    Cleaning()
    

    
