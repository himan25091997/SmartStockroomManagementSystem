
import tkinter as tk
import numpy as np
import csv
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.animation as animation
from matplotlib import style
import time
import datetime
import threading
import random
import queue
import tkinter.font as font
import RPi.GPIO as GPIO

import importlib

GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)

#Ultrasonic Pin Declaration
us_trigger = 24
us_echo = 26
GPIO.setup(us_trigger, GPIO.OUT)
GPIO.setup(us_echo, GPIO.IN)
us_stock=0

#Smoke Pin Declaration
smoke_out = 13
smoke_buzzer = 15
GPIO.setup(smoke_out, GPIO.IN)
GPIO.setup(smoke_buzzer, GPIO.OUT)

#ColorServo Pin Declaration
color_s2 = 16
color_s3 = 18
color_signal = 22
color_NUM_CYCLES = 10
GPIO.setup(color_signal,GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(color_s2,GPIO.OUT)
GPIO.setup(color_s3,GPIO.OUT)
color_servo = 8
GPIO.setup(color_servo, GPIO.OUT)
pwm = GPIO.PWM(color_servo, 50) # GPIO 17 for PWM with 50Hz
pwm.start(7.5) # Initialization


# door servo pin decleration
door_servo = 11
GPIO.setup(door_servo, GPIO.OUT)
pwm1 = GPIO.PWM(door_servo, 50) # GPIO 17 for PWM with 50Hz
pwm1.start(7.5) 

#Entry Password
main_pass = "1234"
length = len(main_pass)
flag=0
led = 3
GPIO.setup(led, GPIO.OUT)

#Keypad Pin Declaration
COL = [32,36,38,40]
ROW = [29,31,33,35]

for j in range(4):
    GPIO.setup(COL[j], GPIO.OUT)
    GPIO.output(COL[j], 1)
for i in range(4):
    GPIO.setup(ROW[i], GPIO.IN, pull_up_down = GPIO.PUD_UP)

#pir pin declaration
GPIO.setup(7,GPIO.IN)

#ir pin declaration
GPIO.setup(12,GPIO.IN)
        

def runnew():
    modulename="directgraph.py"
    importlib.import_module(modulename)

class GuiPart(tk.Frame):
   
    def __init__(self, master, queue, endCommand):
        self.queue = queue
        # Set up the GUI
        tk.Frame.__init__(self, master)
        root.configure(bg='white')  
        root.rowconfigure([0, 1, 2, 3, 4, 5, 6], minsize=50)
        root.columnconfigure([0, 1, 2, 3, 4, 5, 6, 7, 8, 9], minsize=5)
        
        self.myFont1 = font.Font(family='Helvetica', size=18, weight='bold')
        self.myFont2 = font.Font(family='Times', size=15, weight='bold')
        self.label = tk.Label(text="Smart Stockroom Management System", bg="white", fg="black", width=70, height=3)
        self.label['font'] = self.myFont1
        self.label.grid(row=0,columnspan=5)
        
        self.label = tk.Label(text="SUPERVISOR PORTAL", bg="white", fg="black", width=70, height=3)
        self.label['font'] = self.myFont1
        self.label.grid(row=1, columnspan=5)
        
        self.timelabel = tk.Label(bg="white", fg="black", width=70, height=3)
        self.timelabel['font'] = self.myFont2
        self.timelabel.grid(row=2, columnspan=5)  
        
        self.inventorylabel = tk.Label(text="Inventory(%):", fg="black", bg="white", width=15)
        self.inventorylabel['font'] = self.myFont2
        self.inventorylabel.grid(row=3, column=0)
        
        self.invbutton = tk.Button(text="Inventory Graph", command=runnew)
        self.invbutton.grid(row=4, column=0)
        
        self.inventorystat = tk.Label(text="Checking", fg="black", bg="white", width=15)
        self.inventorystat['font'] = self.myFont2
        self.inventorystat.grid(row=3, column=1)
        
        self.smokelabel = tk.Label(text="Smoke Status:", fg="black", bg="white", width=15)
        self.smokelabel['font'] = self.myFont2
        self.smokelabel.grid(row=3, column=3)
        
        self.smokestat = tk.Label(text="Checking", fg="black", bg="white", width=15, justify='left', anchor='w')
        self.smokestat['font'] = self.myFont2
        self.smokestat.grid(sticky='W',row=3, column=4)
        
        self.sortinglabel = tk.Label(text="Sorting Status:", fg="black", bg="white", width=15)
        self.sortinglabel['font'] = self.myFont2
        self.sortinglabel.grid(row=5, column=0)
        
        self.sortstat = tk.Label(text="Checking", fg="black", bg="white", width=15)
        self.sortstat['font'] = self.myFont2
        self.sortstat.grid(row=5, column=1)
        
        self.occlabel = tk.Label(text="Occupancy:", fg="black", bg="white", width=15)
        self.occlabel['font'] = self.myFont2
        self.occlabel.grid(row=5, column=3)
        
        self.occnow = tk.Label(text="Checking", fg="black", bg="white", width=15, justify= 'left', anchor='w')
        self.occnow['font'] = self.myFont2
        self.occnow.grid(sticky='W', row=5, column=4)
        
        console = tk.Button(master, text='Done', command=endCommand)
        console.grid(row=6,columnspan=5)
        

    def processIncoming(self):
        """
        Handle all the messages currently in the queue.
        """
        while self.queue.qsize():
            try:
                result = self.queue.get(0)
                msg = result[0]
                smoke_status = result[1]
                sort_stat=result[2]
                occupancy=result[3]
                t=result[4]
                # Check contents of message
                
                self.inventorystat['text'] = msg
                self.smokestat['text'] = smoke_status
                if(smoke_status=="FIRE!"):
                    self.smokestat['fg'] = 'red'
                if(smoke_status=="Safe"):
                    self.smokestat['fg'] = 'green'
                self.sortstat['text'] = sort_stat
                self.occnow['text'] = occupancy
                self.timelabel['text']=t
                print("inventory: ", msg)
                print("Smoke: ", smoke_status)
                print("Sort: ", sort_stat)
                print("Occupancy: ", occupancy)
            except queue.Empty:
                pass


class ThreadedClient:
    
    def __init__(self, master):
        """
        Start the GUI and the asynchronous threads. We are in the main
        (original) thread of the application, which will later be used by
        the GUI. We spawn a new thread for the worker.
        """
        self.master = master

        # Create the queue
        self.queue = queue.Queue()

        # Set up the GUI part
        self.gui = GuiPart(master, self.queue, self.endApplication)

        # Set up the thread to do asynchronous I/O
        self.running = 1
        self.thread1 = threading.Thread(target=self.combineThread)
        self.thread1.start()

        # Start the periodic call in the GUI to check if the queue contains
        # anything
        self.periodicCall()

    def periodicCall(self):
        """
        Check every 100 ms if there is something new in the queue.
        """
        self.gui.processIncoming()
        if not self.running:
            # This is the brutal stop of the system.
            import sys
            sys.exit(1)
        self.master.after(100, self.periodicCall)

    def ultrasonic(self):
            GPIO.output(us_trigger, True)
         
            time.sleep(0.00001)
            GPIO.output(us_trigger, False)
         
            StartTime = time.time()
            StopTime = time.time()
         
            while GPIO.input(us_echo) == 0:
                StartTime = time.time()
         
            while GPIO.input(us_echo) == 1:
                StopTime = time.time()
         
            TimeElapsed = StopTime - StartTime
            distance = (TimeElapsed * 34300) / 2
            distance = round(distance,2)
            time.sleep(0.2)
            
            msg=((14-distance)*100)/14
            msg = round(msg)    
            if(msg<0):
                msg=0
            return msg
       
            
    def smoke_detect(self):
            stat = GPIO.input(smoke_out)
            if(stat == 1):
                smoke_status = "Safe"
                GPIO.output(smoke_buzzer, False)
                 
            if(stat!=1):
                smoke_status = "FIRE!"
                self.buzz()
                
            return smoke_status
            
    def color_detect(self):
        GPIO.output(color_s2,GPIO.LOW)
        GPIO.output(color_s3,GPIO.LOW)
        time.sleep(0.3)
        start = time.time()
        for impulse_count in range(color_NUM_CYCLES):
            GPIO.wait_for_edge(color_signal, GPIO.FALLING)
        duration = time.time() - start 
        red  = color_NUM_CYCLES / duration   
       
        GPIO.output(color_s2,GPIO.LOW)
        GPIO.output(color_s3,GPIO.HIGH)
        time.sleep(0.3)
        start = time.time()
        for impulse_count in range(color_NUM_CYCLES):
            GPIO.wait_for_edge(color_signal, GPIO.FALLING)
        duration = time.time() - start
        blue = color_NUM_CYCLES / duration
        

        GPIO.output(color_s2,GPIO.HIGH)
        GPIO.output(color_s3,GPIO.HIGH)
        time.sleep(0.3)
        start = time.time()
        for impulse_count in range(color_NUM_CYCLES):
            GPIO.wait_for_edge(color_signal, GPIO.FALLING)
        duration = time.time() - start
        green = color_NUM_CYCLES / duration
        
        sort_stat="Idle"
        if green<7000 and blue<7000 and red>10000:
            sort_stat="In progess red"
            pwm.ChangeDutyCycle(12.5)
            time.sleep(0.5)
            pwm.ChangeDutyCycle(7.5)
            
        elif red<30000 and  blue>30000 and green>30000:
            sort_stat="In progress green"
            
        elif green<9000 and red<9000 and blue>11000:
            sort_stat="In progress blue"
            pwm.ChangeDutyCycle(2.5)
            time.sleep(0.5)
            pwm.ChangeDutyCycle(7.5)
            
        elif red>30000 and green>30000 and blue>30000:
            sort_stat="Idle"

        return sort_stat
    
    def check_intruder(self):
        occupancy="Checking"
        GPIO.output(led, False)
        flag=0
        if (self.ir_detect()==0):
            print("Please Enter User Password: ")
            result = self.check_keypad(length)
            #Password Check
            if result == main_pass:
                print("Open door")
                occupancy="Authorised"
                GPIO.output(led, True)
                pwm1.ChangeDutyCycle(2.5)
                time.sleep(2)
                pwm1.ChangeDutyCycle(7.5)
                flag=1            

            else:
                print("Stay locked")

        if (flag==0 and self.pir_detect()==1):    
            occupancy="Unauthorised"
            
        return occupancy
    
    def pir_detect(self):
        i=0
        i=GPIO.input(7)
        if(i==0):                 
            print ("No intruders inside",i)
            GPIO.output(15, False)
            
            time.sleep(0.1)     
        elif(i==1):               
            print ("Intruder detected",i)
            self.buzz()
        
        return i

#Function to check keypad input!
    def check_keypad(self,length):
        count=0
        COL = [32,36,38,40]
        ROW = [29,31,33,35]

        MATRIX = [["1","2","3","A"],
                  ["4","5","6","B"],
                  ["7","8","9","C"],
                  ["0","F","E","D"]]
        result = ""
        while(True):
            count = count+1
            if(count==300000):
                print("timeout")
                break
            for j in range(4):
                GPIO.output(COL[j], 0)

                for i in range(4):
                    if GPIO.input(ROW[i]) == 0:
                        time.sleep(0.02)
                        result = result + MATRIX[i][j]
                        while(GPIO.input(ROW[i]) == 0):
                              time.sleep(0.02)

                GPIO.output(COL[j], 1)
                if len(result) >= length:
                    return result

    def ir_detect(self):
        if(GPIO.input(12)==True): #object is far away
            ir_stat=1
            print("No one at entrance")
           
        elif(GPIO.input(12)==False): #object is near
            ir_stat=0
            print("Someone at entrance")
            
        return ir_stat

    def write_to_csv(self, occupancy):
        with open("/home/pi/Desktop/distance.csv", mode="a") as sensor_readings:
            sensor_write = csv.writer(sensor_readings, delimiter=",", quotechar="'", quoting=csv.QUOTE_MINIMAL)
            write_to_log = sensor_write.writerow([self.time_now(),self.ultrasonic(),occupancy, self.smoke_detect()])
        return(write_to_log)
#     
    def time_now(self):
        now = datetime.datetime.now().strftime("%H:%M:%S")
        now = str(now)
        return(now)
    
    
    def current_t(self):
        return time.strftime("Date: %d.%m.%Y   Time: %H:%M:%S", time.localtime())
    
    def buzz(self):
         GPIO.output(15, True)  
         time.sleep(0.1)
    
    def combineThread(self):
        entrytime=time.time()
        occupancy="Checking"
        occflag=0
        writeflag=0
        while self.running:
            if(occflag==10):
                occflag=0
            msg=self.ultrasonic()
            smoke_status=self.smoke_detect()
            sort_stat=self.color_detect()
            if(occflag==0):
                if(self.ir_detect()==0):
                    entrytime=time.time()
                    occupancy = self.check_intruder()
                currenttime=time.time()
                intime=round(currenttime-entrytime)
                print("intime: ", intime)
                if(intime>20):
                    occupancy = self.check_intruder()
            if(occupancy=="Unauthorised"):
                occflag=occflag+1
                self.buzz()
            elif(occupancy!="Unauthorised"):
                occflag=0
            t=self.current_t()
            self.queue.put((msg,smoke_status,sort_stat,occupancy, t))
            self.write_to_csv(occupancy)
            print("Ultrasonic: ", msg, writeflag)
            

    def endApplication(self):
        self.running = 0

rand = random.Random()

root = tk.Tk()

client = ThreadedClient(root)
root.title("Smart Stockroom Management System")
root.mainloop()

