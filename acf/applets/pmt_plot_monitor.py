import numpy as np
import PyQt5
import pyqtgraph as pg
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QPushButton, QVBoxLayout, QWidget

from artiq.applets.simple import TitleApplet, SimpleApplet
'''
class PMTPlotMonitor(pg.PlotWidget):

    def __init__(self, args, req):
        pg.PlotWidget.__init__(self)
        self.args = args

        self.pmt_dataset_name = self.args.PMT_count

        self.pmt = []
        self.plotting = False  # State to track if plotting is active

        title = "PMT Count Monitor"

        self.setLabel("bottom", 'index')
        self.setLabel("left", self.pmt_dataset_name)
        self.setTitle(title)
        self.setBackground('k')
        #.setBackground(QColor(240, 240, 240))

        self.pen = pg.mkPen(color=(0, 255, 0))

        # Create buttons
        self.start_stop_button = QPushButton("Start")
        self.clear_button = QPushButton("Clear")

        # Connect buttons to functions
        # self.start_stop_button.clicked.connect(self.start_stop_plot)
        # self.clear_button.clicked.connect(self.clear_plot)

        # Set up layout
        self.layout = QVBoxLayout()
        self.layout.addWidget(self)
        self.layout.addWidget(self.start_stop_button)
        self.layout.addWidget(self.clear_button)

        self.setLayout(self.layout)
    
    def start_stop_plot(self):
        if self.plotting:
            self.plotting = False
            self.start_stop_button.setText("Start")
        else:
            self.plotting = True
            self.start_stop_button.setText("Stop")

    def clear_plot(self):
        self.pmt = []
        self.clear()
        

    def data_changed(self, value, metadata, persist, mod_buffer):
        if self.pmt_dataset_name not in value:
            raise RuntimeError(f"Y Dataset name '{self.pmt_dataset_name}' "
                                "not in value.")

        y_data = value[self.pmt_dataset_name][0]

        self.pmt.append(y_data)

        x_data = np.arange(len(self.pmt))

        if len(self.pmt)>5e5:
            self.pmt=[]
        
        if self.plotting: 
            self.clear()
            plot=self.plot(x_data, self.pmt, pen=self.pen, symbol="o")
            plot.setSymbolSize(5)
            plot.setSymbolBrush((255, 0, 0))  # Set the color of the symbol (fluorescent pink)
'''

from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QHBoxLayout
import pyqtgraph as pg
import numpy as np

class PMTPlotMonitor(QWidget):

    def __init__(self, args, req):
        super().__init__()
        self.args = args

        self.pmt_dataset_name = self.args.PMT_count
        self.pmt = []
        self.plotting = False  # State to track if plotting is active

        # Set up the main widget layout
        main_layout = QVBoxLayout()

        # Create a PlotWidget
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setLabel("bottom", 'index')
        self.plot_widget.setLabel("left", self.pmt_dataset_name)
        self.plot_widget.setTitle("PMT Count Monitor")
        self.plot_widget.setBackground('k')
        self.pen = pg.mkPen(color=(0, 255, 0))
        
        # Create a horizontal line at y=0 for reference
        self.zero_line = pg.InfiniteLine(pos=0, angle=0, pen=pg.mkPen(color=(255, 255, 255), style=pg.QtCore.Qt.DashLine))
        self.plot_widget.addItem(self.zero_line)

        # Add the plot widget to the main layout
        main_layout.addWidget(self.plot_widget)

        # Create buttons
        self.start_stop_button = QPushButton("Start")
        self.clear_button = QPushButton("Clear")

        # Connect buttons to functions
        self.start_stop_button.clicked.connect(self.start_stop_plot)
        self.clear_button.clicked.connect(self.clear_plot)

        # Set up button layout
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.start_stop_button)
        button_layout.addWidget(self.clear_button)

        # Add button layout to the main layout
        main_layout.addLayout(button_layout)

        # Set the layout for the main widget
        self.setLayout(main_layout)

    def start_stop_plot(self):
        if self.plotting:
            self.plotting = False
            self.start_stop_button.setText("Start")
        else:
            self.plotting = True
            self.start_stop_button.setText("Stop")

    def clear_plot(self):
        self.pmt = []
        self.plot_widget.clear()
        # Re-add the zero line after clearing
        self.plot_widget.addItem(self.zero_line)

    def data_changed(self, value, metadata, persist, mod_buffer):
        if self.pmt_dataset_name not in value:
            raise RuntimeError(f"Y Dataset name '{self.pmt_dataset_name}' "
                               "not in value.")

        y_data = value[self.pmt_dataset_name][0]
        self.pmt.append(y_data)

        if len(self.pmt) > 5e4:
            self.pmt = []

        if self.plotting:  # Only plot if plotting is active
            x_data = np.arange(len(self.pmt))
            self.plot_widget.clear()
            # Re-add the zero line after clearing
            self.plot_widget.addItem(self.zero_line)
            plot = self.plot_widget.plot(x_data, self.pmt, pen=self.pen, symbol="o")
            plot.setSymbolSize(5)
            plot.setSymbolBrush((255, 0, 0))  # Set the color of the symbol

def main():
    applet = SimpleApplet(PMTPlotMonitor)
    #applet = TitleApplet(ExperimentMonitor)
    applet.add_dataset("PMT_count", "PMT Count Value")
    applet.run()


if __name__ == "__main__":
    main()
