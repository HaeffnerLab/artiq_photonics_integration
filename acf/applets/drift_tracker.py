import numpy as np
import PyQt5
import pyqtgraph as pg
from PyQt5.QtGui import QColor

from artiq.applets.simple import TitleApplet, SimpleApplet


import time
from collections import deque
# timestamp_ms = int(time.time() * 1000)
# print(timestamp_ms)

class Drift_Tracker(pg.PlotWidget):

    def __init__(self, args, req):
        pg.PlotWidget.__init__(self)
        self.args = args
        self.req =req

        self.time_now=time.time()
        self.freq_qubit_dataset_name = self.args.freq_qubit
        self.freq_qubit_err_dataset_name = self.args.freq_qubit_err

        #queue for saving the frequency tag
        L=100
        self.queue_freq = deque(maxlen=L) 
        self.queue_freq_err = deque(maxlen=L)
        self.queue_time = deque(maxlen=L)

        title = "Drift_Tracker"

        self.setLabel("bottom", 'time(s)')
        self.setLabel("left", 'freq_qubit(MHz)')
        self.setTitle(title)
        self.setBackground('k')
        #.setBackground(QColor(240, 240, 240))
        
        self.waiting_for_size_update = False
    
    def fit_quadratic(self, t, f):
        # Fit quadratic curve (degree 2 polynomial)
        coeffs = np.polyfit(t, f, 2)  # Returns [a, b, c]
        return coeffs[0], coeffs[1], coeffs[2]  # Extract a, b, c

    def data_changed(self, value, metadata, persist, mod_buffer):
        
        # if self.y_dataset_name not in value:
        #     raise RuntimeError(f"Y Dataset name '{self.y_dataset_name}' "
        #                         "not in value.")

        #get the new qubit frequency & uncertainty
        qubit_freq_now = value[self.freq_qubit_dataset_name]
        #qubit_freq_err_now = value[self.freq_qubit_err_dataset_name]
        
    
        self.queue_freq.append(qubit_freq_now)
        #self.queue_freq_err.append(qubit_freq_err_now)
        self.queue_time.append(time.time())


        self.clear()
        self.addLegend()
        plot=self.plot(np.array(self.queue_time)-self.time_now,np.array(self.queue_freq),  symbol="o", name='measure')
        plot.setSymbolSize(5)
        plot.setSymbolBrush((255, 0, 0))  # Set the color of the symbol (fluorescent pink)

        # Find data points within last hour
        current_time = time.time()
        one_hour_ago = current_time - 3600  # 3600 seconds = 1 hour
        
        # Get indices of points within last hour
        recent_indices = [i for i, t in enumerate(self.queue_time) if t > one_hour_ago]
        
        # Get recent points
        recent_times = np.array(self.queue_time)[recent_indices] 
        recent_freqs = np.array(self.queue_freq)[recent_indices]
        
        # Fit with at^2+bt+c if we have enough recent points
        if len(recent_indices) > 5:
            a, b, c = self.fit_quadratic(recent_times, recent_freqs)
        else:
            a, b, c = 0, 0, qubit_freq_now


        self.req.set_dataset('__param__tracker/qubit/a', a)
        self.req.set_dataset('__param__tracker/qubit/b', b)
        self.req.set_dataset('__param__tracker/qubit/c', c)
        

        plot=self.plot(np.array(self.queue_time)-self.time_now,a*np.array(self.queue_time)**2+b*np.array(self.queue_time)+c, pen='b', name='predict')
        plot.setSymbolSize(5)

     


def main():
    applet = SimpleApplet(Drift_Tracker)
    applet.add_dataset("freq_qubit", "Y values")
    applet.add_dataset("freq_qubit_err", "Y values uncertainty", required=False)
    
    applet.run()


if __name__ == "__main__":
    main()
