import time

class cTimer():
    def __init__(self):
        self.time = 0
        self.delay = 0
    
    def Start(self,delay): #start timer with given delay in secs
        self.time = time.time()
        self.delay = delay
        self.started=True
        
    def Expired(self): # test if timer has expired        
        return (time.time() - self.time)>=self.delay