#!/usr/bin/python3

import time

class StateMachine:
    
    def __init__(self,stateList):
        self.stateList = stateList
        self.currState = ""#for first execution it is zero
        self.nextState = stateList[0]
        self.__stepTime = time.time()
        self.__acumulatedTimeList = [0]*len(stateList)
        self.__1secTmr = 0
        self.__first=True#true always for first execution of step

    def NextState(self,name = ""):

        if name == "":
            idx = self.stateList.index(self.currState)
            idx = idx + 1
            self.nextState = self.stateList[idx]
        elif not name in self.stateList:
            raise Exception("State:"+str(name)+" doesn't exists !")
        else:
            self.nextState = name

    def Run(self):
        if self.nextState != "" and self.currState != self.nextState:
            print("Transition to:"+self.nextState.__name__)
            self.currState = self.nextState
            self.__stepTime = time.time()
            self.__first=True


        #incerement each 1 sec - accumulated time for each step
        if time.time() - self.__1secTmr>1.0:
            self.__acumulatedTimeList[self.stateList.index(self.currState)]+=1
            
            self.__1secTmr = time.time()

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
    
    def getAcumulatedTime(self):#return acumulated time of current state
        
        return self.__acumulatedTimeList[self.stateList.index(self.currState)]
    
    def ResetAcumulatedTime(self):
        self.__acumulatedTimeList[self.stateList.index(self.currState)]=0
