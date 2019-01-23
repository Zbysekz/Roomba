#!/usr/bin/python3

from comm import *
from sys import stdout
import sys
from time import sleep


def RunLogic():
    try:
        while(1):
            bmsData = ReadBMSData()

            sensorData = ReadMotherBoardData();

            if(sensorData ==[] or bmsData==[]):
                Move(0,0)
                print("EMPTY DATA!")
                sleep(1)
                continue
            
            somethingClose = any([s>0.3 for s in sensorData[0]])
            
            liftedUp = not sensorData[3]!=0 or not sensorData[4]!=0#wheel switches
            
            onCliff = any([s<0.5 for s in sensorData[1]])

            print(str(sensorData[0])+" --- "+str(somethingClose)+" "+str(liftedUp)+" "+str(onCliff))
            if not somethingClose and not liftedUp and not onCliff:
                Move(40,40)
            else:
                Move(0,0)
            
            sleep(0.05)
    except KeyboardInterrupt:
        Move(0,0)
        print("Keyboard interrupt, stopping!")

if __name__ == "__main__":   

    Init();

    if(len(sys.argv)>1):
        if('BMS' in sys.argv[1]):
            ShowBMSData()
        elif('MOTHER' in sys.argv[1]):
            Move(0,0)
            ShowMotherBoardData()
        elif('RUN' in sys.argv[1]):
            RunLogic()

        