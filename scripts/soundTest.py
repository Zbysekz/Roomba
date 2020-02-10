import os
import threading


def playSound(filename):
    print("Playing sound:"+filename)
    os.system('aplay '+filename)
    

threading.Thread(target=playSound, args=('sounds/startup.wav',)).start()




