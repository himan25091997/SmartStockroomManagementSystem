import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.animation as animation
from matplotlib import style
import tkinter as tk
from tkinter import ttk

style.use("ggplot")

f = Figure(figsize=(5,5), dpi=100)
a = f.add_subplot(111)

def animate(i):
    pullData = open("datadump.csv","r").read()
    dataList = pullData.split('\n')
    xList = []
    yList = []
    mList = []
    nList = []
    for eachLine in dataList:
        if len(eachLine) > 1:
            x, y, m, n = eachLine.split(',')
            xList.append(x)
            yList.append(int(y))
            mList.append(m)
            nList.append(n)

    a.clear()
    a.plot(xList, yList)

class Graph(tk.Tk):

    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)
    
        
        canvas = FigureCanvasTkAgg(f, self)
        canvas.draw()
        canvas.get_tk_widget().pack()
        canvas._tkcanvas.pack()


app = Graph()
ani = animation.FuncAnimation(f, animate, interval=10)
app.title("Inventory Graph")
app.mainloop()
        
        
