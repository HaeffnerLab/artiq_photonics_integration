import numpy as np
import PyQt5
import pyqtgraph as pg
from PyQt5.QtGui import QColor

from artiq.applets.simple import TitleApplet, SimpleApplet

class ExperimentMonitor(pg.PlotWidget):

    def __init__(self, args, req):
        pg.PlotWidget.__init__(self)
        self.args = args

        self.y_dataset_name = self.args.y
        self.has_x_dataset = self.args.x is not None
        self.has_fit_dataset = self.args.fit is not None
        self.has_err_dataset = self.args.y_err is not None

        if self.has_x_dataset:
            self.x_dataset_name = self.args.x
        else:
            self.x_dataset_name = "No X Dataset"
        
        if self.has_fit_dataset:
            self.fit_dataset_name = self.args.fit
        else:
            self.fit_dataset_name = "No Fit Dataset"

        if self.has_err_dataset:
            self.err_dataset_name = self.args.y_err
        else:
            self.err_dataset_name = "No Error Dataset"

        if self.args.xmax is not None and not self.has_x_dataset:
            raise RuntimeError("xmax given, but no x dataset given.")

        # This assume the default value of xmin and xmax is 0
        if self.args.xmin != 0 and self.args.xmax is None:
            raise RuntimeError("xmin given but no xmax given.")
        if self.args.ymin != 0 and self.args.ymax is None:
            raise RuntimeError("ymin given but no ymax given.")

        if self.args.xmax is not None:
            self.setXRange(self.args.xmin, self.args.xmax)
        if self.args.ymax is not None:
            self.setYRange(self.args.ymin, self.args.ymax)
        
        if not self.args.pen:
             self.pen = None
        else:
             self.pen = pg.mkPen(color=(0, 255, 0))#1

        title = "Experiment Monitor"
        if self.args.exp_label is not None:
             title += f"<br>({self.args.exp_label})"

        self.setLabel("bottom", self.x_dataset_name)
        self.setLabel("left", self.y_dataset_name)
        self.setTitle(title)
        self.setBackground('k')
        #.setBackground(QColor(240, 240, 240))
        
        self.waiting_for_size_update = False

    def data_changed(self, value, metadata, persist, mod_buffer):
        if self.y_dataset_name not in value:
            raise RuntimeError(f"Y Dataset name '{self.y_dataset_name}' "
                                "not in value.")

        if self.has_x_dataset and self.x_dataset_name not in value:
            raise RuntimeError(f"X Dataset name '{self.x_dataset_name}' "
                                "not in value.")

        if self.has_fit_dataset and self.fit_dataset_name not in value:
            raise RuntimeError(f"Fit Dataset name '{self.fit_dataset_name}' "
                                "not in value.")       

        y_data = value[self.y_dataset_name]
        if self.has_x_dataset:
            x_data = value[self.x_dataset_name]
        else:
            x_data = np.arange(len(y_data))
        
        if self.has_fit_dataset:
            fit_data=value[self.fit_dataset_name]

        if self.has_err_dataset:
            err_data=value[self.err_dataset_name]
        
        # If x_data and y_data have different lengths, wait one update cycle
        # to see if the other has updated to the right length. Else raise an error.
        if x_data.size != y_data.size:
            if not self.waiting_for_size_update:
                self.waiting_for_size_update = True
                return
            else:
                raise RuntimeError(
                    f"Size mismatch between x_data ({x_data.size}) "
                    f"and y_data ({y_data.size})."
                )
        
        # If we waited for a size update and sizes matched, unset this flag
        elif self.waiting_for_size_update:
            self.waiting_for_size_update = False

        self.clear()
        plot=self.plot(x_data, y_data, pen=self.pen, symbol="o")
        plot.setSymbolSize(5)
        plot.setSymbolBrush((255, 0, 0))  # Set the color of the symbol (fluorescent pink)

        
        if self.has_fit_dataset:
           self.plot(x_data, fit_data, pen='r')#, symbol='o').setSymbolSize(5)



def main():
    applet = SimpleApplet(ExperimentMonitor)
    #applet = TitleApplet(ExperimentMonitor)
    applet.add_dataset("y", "Y values")
    applet.add_dataset("y_err", "Y values uncertainty", required=False)
    applet.add_dataset("x", "X values", required=False)
    applet.add_dataset("fit"," The fitted values", required=False)

    applet.argparser.add_argument("--xmin", type=float, default=0,
                                  help="Min value of the x axis")
    applet.argparser.add_argument("--xmax", type=float, default=None,
                                  help="Max value of the x axis")
    applet.argparser.add_argument("--ymin", type=float, default=0,
                                  help="Min value of the y axis")
    applet.argparser.add_argument("--ymax", type=float, default=None,
                                  help="Max value of the y axis")
    applet.argparser.add_argument("--pen", type=bool, default=False,
                                  help="Set to true to draw lines between points.")
    applet.argparser.add_argument("--exp-label", type=str, default=None)
    applet.run()


if __name__ == "__main__":
    main()
