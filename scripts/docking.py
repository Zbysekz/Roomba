#!/usr/bin/python3
from roombaPlatform import Platform
from time import sleep
import time

goodDirection = 0
reversing = 0

oscilState=False
tmrOscil=0
steer=0
lastTimeCharging=0
baseIsClose=False
rightBaseBeam=0
leftBaseBeam=0


def Dock():
        
    leftIRrate = pl.getLeftRate()
    rightIRrate = pl.getRightRate()
    topIRrate = pl.getTopRate()
    
    #print("L:"+str(leftIRrate[0])+","+str(leftIRrate[1])+","+str(leftIRrate[2]))
    #print("R:"+str(rightIRrate[0])+","+str(rightIRrate[1])+","+str(rightIRrate[2]))
    #print("T:"+str(topIRrate[0])+","+str(topIRrate[1])+","+str(topIRrate[2]))
    
    baseIsClose = True if topIRrate[Platform.TOP]>0 else False
    

    if leftBaseBeam > 0:
        leftBaseBeam-=1
    if rightBaseBeam > 0:
        rightBaseBeam-=1
    
        
    #leftBaseBeam = True if topIRrate[Platform.LEFT]>0 else False
    #rightBaseBeam = True if topIRrate[Platform.LEFT]>0 else False
    

    if not pl.isCharging and not pl.liftedUp and not pl.onCliff: #not pl.somethingClose and           
        
        if reversing>0:
            reversing-=1
        elif pl.bumper:
            pl.Move(0,0)
            sleep(1)
            
            #but if there was charging signal just before bump, go back a little
            if time.time() - lastTimeCharging < 5:
                pl.Move(-10,-10,distance=15)
                reversing=10
            else:
                pl.Move(-60,-60,distance=40)
                reversing=12
    
    
        elif goodDirection>0:
            goodDirection-=1
            pl.Move(20,20)
            print("UUUUU")
            
        elif leftIRrate[Platform.LEFT]==0 and leftIRrate[Platform.RIGHT]!=0 and\
            rightIRrate[Platform.LEFT]==0 and rightIRrate[Platform.RIGHT]!=0:
        
            pl.Move(20,12) #(1)
            print("R(1)")
    
        elif leftIRrate[Platform.LEFT]!=0 and leftIRrate[Platform.RIGHT]==0 and\
            rightIRrate[Platform.LEFT]!=0 and rightIRrate[Platform.RIGHT]==0:
        
            pl.Move(12,20) #(2)
            print("L(2)")
        
        elif leftIRrate[Platform.LEFT]==0 and leftIRrate[Platform.RIGHT]==0 and\
            (rightIRrate[Platform.LEFT]!=0 or rightIRrate[Platform.RIGHT]!=0):
            
            if rightIRrate[Platform.LEFT] < rightIRrate[Platform.RIGHT]:
                pl.Move(20,12) #(3)
                print("R(3)")
            else:
                pl.Move(20,12) #(4)
                print("R(4)")
    
        elif rightIRrate[Platform.LEFT]==0 and rightIRrate[Platform.RIGHT]==0 and\
            (leftIRrate[Platform.LEFT]!=0 or leftIRrate[Platform.RIGHT]!=0):
            
            if leftIRrate[Platform.LEFT] > leftIRrate[Platform.RIGHT]:
                pl.Move(12,20) #(5)
                print("L(5)")
            else:
                pl.Move(12,20) #(6)
                print("L(6)")
        elif rightIRrate[Platform.LEFT]!=0 and leftIRrate[Platform.RIGHT]!=0 :
            
                if rightIRrate[Platform.RIGHT] > leftIRrate[Platform.LEFT]:
                    #go slightly right
                    pl.Move(20,18) #(7)
                    print("F(7)")
                elif rightIRrate[Platform.RIGHT] < leftIRrate[Platform.LEFT]:
                    #go slightly left
                    pl.Move(18,20)
                    print("F(8)")
                else:
                    pl.Move(20,20)
                    print("F(9)")
                
                #goodDirection=8
                print("GOOD DIRECTION!")
#            elif topIRrate[Platform.LEFT]>0:
#                pl.Move(20,10)
#                print("R(10)")
#            elif topIRrate[Platform.RIGHT]>0:
#                pl.Move(10,20)
#                print("L(11)")
        elif topIRrate[Platform.LEFT]>0 or topIRrate[Platform.RIGHT]>0:
        
            if topIRrate[Platform.LEFT]>0:
                if rightBaseBeam>0:
                    pl.Move(-10,30,distance=10)#base is probably on the left
                    print("L(13)")
                    sleep(3)
                else:
                    pl.Move(20,10)
                    print("R(10)")
                    leftBaseBeam=40
    
            if topIRrate[Platform.RIGHT]>0:
                if leftBaseBeam>0:
                    pl.Move(30,-10,distance=10)#base is probably on the right
                    print("R(12)")
                    sleep(3)
                else:
                    rightBaseBeam=40
                    pl.Move(10,20)
                    print("L(11)")
        else:
            if baseIsClose:
                pl.Move(15,15)
            else:
                pl.Move(30,30)
            print("(-)")
    
    
    else:
        if pl.isCharging:
            lastTimeCharging = time.time()
        pl.Move(0,0)
        #print("(S)"+str(pl.somethingClose)+" "+str(pl.liftedUp) +" "+ str(pl.onCliff))
        
    sleep(0.1)
    


if __name__ == "__main__":

    pl = Platform()

    pl.Connect()

    while(1):
        pl.Preprocess()
        Dock(pl)
        pl.RefreshTimeout()
    except KeyboardInterrupt:
        pl.Move(0,0)
        print("Keyboard interrupt, stopping!")
    
    pl.Terminate()
    
    print("END")

        

    
