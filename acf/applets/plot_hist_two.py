#!/usr/bin/env python3

import PyQt5    # make sure pyqtgraph imports Qt5
from PyQt5.QtCore import QTimer
import pyqtgraph
import pyqtgraph as pg
from artiq.applets.simple import TitleApplet
import numpy as np

class HistogramPlot(pyqtgraph.PlotWidget):
    def __init__(self, args, req):
        pyqtgraph.PlotWidget.__init__(self)
        self.args = args
        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.length_warning)

    def data_changed(self, value, metadata, persist, mods, title):
        try:
            y = value[self.args.y]

            if self.args.x is None:
                x = None
            else:
                x = value[self.args.x]
            

            y2= value[self.args.y2]
        except KeyError:
            return
        if x is None:
            x = list(range(len(y)+1))


        
    
        if len(y) and len(x) == len(y) + 1:
            self.timer.stop()
            self.clear()
            # self.plot(x, y, stepMode=True, fillLevel=0,
            #           brush=(0, 0, 255, 150))
            self.setTitle(title)

            # if y2 is not None:
            #     self.plot(x, y2, stepMode=True, fillLevel=0,
            #           brush=(0, 255, 255, 150))
            
            # Plot first histogram: enable step mode for a histogram-like appearance
            # curve1 = pg.PlotCurveItem(x=x, y=y, stepMode=True, fillLevel=0, brush=(0, 0, 255, 100), pen='b')
            # self.addItem(curve1)

            # # Plot second histogram: different color
            # curve2 = pg.PlotCurveItem(x=x, y=y2, stepMode=True, fillLevel=0, brush=(255, 0, 0, 100), pen='r')
            # self.addItem(curve2)

            # Plot the first histogram
            curve1 = pg.PlotCurveItem(x=x, y=y, 
                                      stepMode=True, fillLevel=0, 
                                      brush=(255, 0, 0, 100), pen='r')
            self.addItem(curve1)

            # If we have a second histogram, plot it in another color
            if y2 is not None:
                curve2 = pg.PlotCurveItem(x=x, y=y2, 
                                            stepMode=True, fillLevel=0, 
                                            brush=(0, 0, 255, 100), pen='b')
                                            
                self.addItem(curve2)

           # print(len(y), len(y2), np.argmax(y), np.argmax(y2), np.sum(y), np.sum(y2))



            # Add threshold line if applicable
            # try:
            #     if self.args.threshold is not None:
            #         threshold = value[self.args.threshold]
            #         threshold_line = pg.InfiniteLine(
            #             pos=threshold, angle=90,
            #             pen=pg.mkPen(color="r", width=2)
            #         )
            #         self.addItem(threshold_line)

            #         # Add label for the threshold line
            #         threshold_label = pg.TextItem(
            #             text=f"Threshold: {threshold:.2f}",  # Format to 2 decimal places
            #             anchor=(0, 1), color="r"
            #         )
            #         self.addItem(threshold_label)
                    
            #         # Position the label near the threshold line
            #         y_pos = np.max(y)/2
            #         threshold_label.setPos(threshold, y_pos + 0.5)  # Adjust for visibility
                    
            # except KeyError:
            #     print(f"Threshold key '{self.args.threshold}' not found in data")
            
            #self.enableAutoRange('xy', True)

        else:
            if not self.timer.isActive():
                self.timer.start(1000)
        
        


    def length_warning(self):
        self.clear()
        text = "⚠️ dataset lengths mismatch:\n"\
            "There should be one more bin boundaries than there are Y values"
        self.addItem(pyqtgraph.TextItem(text))


def main():
    applet = TitleApplet(HistogramPlot)
    applet.add_dataset("y", "Y values")
    applet.add_dataset("y2", "Y2values", required=False)
    applet.add_dataset("x", "Bin boundaries", required=False)
    #applet.add_dataset("threshold", "threshold", required= False)
    applet.run()

if __name__ == "__main__":
    main()