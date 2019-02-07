#!/usr/bin/python3

import time

class StateMachine:
    
    def __init__(self,stateList):
        self.stateList = stateList
        self.currState = stateList[0]
        self.nextState = stateList[0]
        self.__stepTime = time.time()
        self.__first=True#true always for first execution of step

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
            self.__stepTime = time.time()
            self.__first=True

        # Execute the function
        self.currState()

    def getStepTime(self):#in seconds
        return time.time() - self.__stepTime
    
    def ResetStepTime(self):
        self.__stepTime=time.time()
    
    def First(self):
        ret = self.__first
        self.__first=False
        return ret
