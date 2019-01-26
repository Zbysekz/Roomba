#!/usr/bin/python3
from roombaPlatform import Platform
from time import sleep


pl = Platform()

pl.Connect()


goodDirection = 0
reversing = 0

try:
    while(1):
        pl.Preprocess()
        
        
        leftIRrate = pl.getLeftRate()
        rightIRrate = pl.getRightRate()
        topIRrate = pl.getTopRate()
        
        #print("L:"+str(leftIRrate[0])+","+str(leftIRrate[1])+","+str(leftIRrate[2]))
        #print("R:"+str(rightIRrate[0])+","+str(rightIRrate[1])+","+str(rightIRrate[2]))
        #print("T:"+str(topIRrate[0])+","+str(topIRrate[1])+","+str(topIRrate[2]))
        
    
        if not pl.isCharging and not pl.liftedUp and not pl.onCliff: #not pl.somethingClose and 
        
            if reversing>0:
                reversing-=1
            elif pl.bumper:
                pl.Move(-40,-40,distance=30)
                reversing=20
        
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
                    pl.Move(20,10) #(3)
                    print("R(3)")
                else:
                    pl.Move(20,12) #(4)
                    print("R(4)")
        
            elif rightIRrate[Platform.LEFT]==0 and rightIRrate[Platform.RIGHT]==0 and\
                (leftIRrate[Platform.LEFT]!=0 or leftIRrate[Platform.RIGHT]!=0):
                
                if leftIRrate[Platform.LEFT] > leftIRrate[Platform.RIGHT]:
                    pl.Move(10,20) #(5)
                    print("L(5)")
                else:
                    pl.Move(12,20) #(6)
                    print("L(6)")
            elif rightIRrate[Platform.LEFT]!=0 and leftIRrate[Platform.RIGHT]!=0 :
                    pl.Move(20,20) #(7)
                    print("F(7)")
                    goodDirection=8
                    print("GOOD DIRECTION!")
            else:
                pl.Move(15,15)
                print("(-)")
        
        
        else:
            pl.Move(0,0)
            print("(S)"+str(pl.somethingClose)+" "+str(pl.liftedUp) +" "+ str(pl.onCliff))
            
        
        
        
        pl.RefreshTimeout()
        
        sleep(0.2)
except KeyboardInterrupt:
    pl.Move(0,0)
    print("Keyboard interrupt, stopping!")
    
    pl.Terminate()
    

print("END")