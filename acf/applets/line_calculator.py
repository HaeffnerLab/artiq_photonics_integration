import sys
import random
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton
import pyqtgraph as pg
import numpy as np
from artiq.applets.simple import TitleApplet, SimpleApplet

from pyqtgraph.Qt import QtGui

muB = 9.274009995*1e-24
h = 6.62607015*1e-34
hbar = h/2/np.pi

def Zeeman_Enrg(B, mS, mD, gS, gD, linecentre:float):
    '''
    linecentre: in MHz (without 2pi)
    '''
    
    freq1 =B*gS*mS*muB/(h*1e6)

    freq2 =B*gD*mD*muB/(h*1e6)
                                
    return linecentre+freq2-freq1

def Solve_B(mS1, mD1, mS2, mD2, gS, gD, freq_1, freq_2):
    '''
    freq_1: MHz = B*g['D52']*mD1*muB/(h*10^6) -B*g['S12']*mS1*muB/(h*10^6) + linecenter
    freq_2: MHz = B*g['D52']*mD2*muB/(h*10^6) -B*g['S12']*mS2*muB/(h*10^6) + linecenter
    '''

    B_field= (freq_1-freq_2)/(gD*mD1*muB/(h*1e6) -gS*mS1*muB/(h*1e6) - gD*mD2*muB/(h*1e6) +gS*mS2*muB/(h*1e6) )

    linecenter=freq_1-B_field*(gD*mD1*muB/(h*1e6) -gS*mS1*muB/(h*1e6))

    return B_field, linecenter



class LineCalculator(QWidget):
    def __init__(self, args, req):
        super().__init__()

        self.req = req
        
        self.line_pairs=[
            # S , D
            (-1/2.0, -1/2.0),
            (-1/2.0, -5/2.0),
            (1/2.0 , -3/2.0),
            (-1/2,   3/2),
            (1/2,   1/2)
        ]

        # self.line_labels=[
        #     'Sm1_2_Dm1_2',
        #     'Sm1_2_Dm5_2',
        #     'S1_2_D5_2'
        # ]

        self.line_labels = ['S-1/2 D-1/2', 'S-1/2 D-5/2', 'S1/2 D-3/2', 'S-1/2 D3/2', 'S1/2 D1/2']

        self.g_factor={
            'S1_2':2., 
            'D5_2':6/5.0
        }

        self.lines=[]

        self.B=0 # in Gauss
        self.linecenter = 0#in MHz

        if args.Sm1_2_Dm5_2 is None:
            raise RuntimeError("S -1/2 -> D -5/2 line missing")
        
        if args.Sm1_2_Dm1_2 is None:
            raise RuntimeError("S -1/2 -> D -1/2 line missing")

        self.args=args
        
        self.B, self.linecenter = 0,0 
        
        self.line_freq=[0 for i in range(len(self.line_labels))]

        self.calculate_all_lines()

        # Set up the user interface
        self.initUI()

    
    def calculate_all_lines(self):

        for i in range(len(self.line_pairs)):
            self.line_freq[i]=Zeeman_Enrg(self.B, self.line_pairs[i][0], self.line_pairs[i][1], self.g_factor['S1_2'], self.g_factor['D5_2'], self.linecenter)


    def data_changed(self, value, metadata, persist, mod_buffer):
        
        #update the line paramters
        self.Sm1_2_Dm1_2 = value[self.args.Sm1_2_Dm1_2]/10**6*2
        self.Sm1_2_Dm5_2 = value[self.args.Sm1_2_Dm5_2]/10**6*2


        self.B, self.linecenter =Solve_B(-1/2., -1/2., -1/2., -5/2., self.g_factor['S1_2'], self.g_factor['D5_2'], self.Sm1_2_Dm1_2, self.Sm1_2_Dm5_2)
        
        self.calculate_all_lines()

        self.update_lines()


        self.req.set_dataset('__param__qubit/B', self.B*10000)
        self.req.set_dataset('__param__qubit/S1_2_Dm3_2', self.line_freq[2]/2*10**6, unit='MHz')
        self.req.set_dataset('__param__qubit/Sm1_2_S1_2', np.abs(self.B*self.g_factor['S1_2']*muB/(h)), unit='MHz')

    def initUI(self):
        # Create a vertical layout
        layout = QVBoxLayout()
        
        # Create a PlotWidget
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setRange(yRange=(0, 1),xRange=(230,240))
        layout.addWidget(self.plot_widget)
        

        self.text_items_top = []
        self.text_items_bottom = []
        
        for i, label in enumerate(self.line_labels):
            x = self.line_freq[i]/2  # Initial x positions
            line = self.plot_widget.plot([x, x], [0, 1], pen='r')

            text_top = pg.TextItem(text=f'{self.line_freq[i]}', anchor=(0.5, -1.5))
            text_bottom = pg.TextItem(text=f'{label}', anchor=(0.5, 1.5))

            text_top.setPos(x, 1)
            text_bottom.setPos(x, 0)


            self.plot_widget.addItem(text_top)
            self.plot_widget.addItem(text_bottom)
            
            self.lines.append(line)
            self.text_items_top.append(text_top)
            self.text_items_bottom.append(text_bottom)

        # Create an x-axis label using LabelItem
        self.x_label = pg.LabelItem(justify='center')
        self.x_label.setText("X Axis: $\\alpha$")
        self.plot_widget.getPlotItem().setLabel('bottom', text='MHz')
        
        # Create a "Calculate" button
        # self.button = QPushButton('Calculate')
        # self.button.clicked.connect(self.update_lines)
        # layout.addWidget(self.button)
        
        # Set the layout
        self.setLayout(layout)
        
        # Set the main window properties
        #self.setWindowTitle('PlotWidget Example')
        self.setGeometry(100, 100, 800, 600)
        
        #self.show()

    def update_lines(self):

        self.calculate_all_lines()

        # Update the vertical lines with new random positions
        for i, (line, text_top, text_bottom) in enumerate(zip(self.lines, self.text_items_top, self.text_items_bottom)):
            x = self.line_freq[i]/2
            line.setData([x, x], [0, 1])
            text_top.setPos(x, 1)
            text_bottom.setPos(x, 0)
            text_top.setText(f'{x:.3f}')
            text_bottom.setText(f'{self.line_labels[i]}')
        

        #, unit=unit_str)


def main():
    applet = SimpleApplet(LineCalculator)
    
    applet.add_dataset("Sm1_2_Dm5_2", "Sm1_2_Dm5_2 line")
    applet.add_dataset("Sm1_2_Dm1_2", "Sm1_2_Dm1_2 line")

    applet.run()



if __name__ == "__main__":
    main()