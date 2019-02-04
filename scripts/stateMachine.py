#!/usr/bin/python3

import time

class StateMachine:
    
    def __init__(self,stateList):
        self.stateList = stateList
        self.currState = stateList[0]
        self.nextState = stateList[0]
        self.tmrTimeout = 0

    def NextState(self,name = ""):

        if name == "":
            idx = self.stateList.index(self.currState)
            idx = idx + 1
            self.nextState = self.stateList[idx]
        else:
            self.nextState = name

    def Run(self):
        if self.currState != "" and self.nextState != "" and self.currState != self.nextState:
            print("Transition to:"+self.nextState.__name__)
            self.currState = self.nextState
            self.ResetTimeout()

        # Execute the function
        self.currState()

    def CheckTimeout(self,timeout):#in seconds

        if time.time() - self.tmrTimeout > timeout:
            return True
        else:
            return False
    def ResetTimeout(self):
        self.tmrTimeout = time.time()
