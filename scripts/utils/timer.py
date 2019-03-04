import time

class cTimer():
    def __init__(self):
        self.time = 0
        self.delay = 0
        self.started = False
    
    def Start(self,delay): #start timer with given delay in secs
        self.time = time.time()
        self.delay = delay
        self.started=True
        
    def Expired(self): # test if timer has expired
        if not self.started:
            return False
        
        return (time.time() - self.time)>=self.delay
    
    def Stop(self):
        self.started=False