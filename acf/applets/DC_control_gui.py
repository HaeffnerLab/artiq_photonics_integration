"""This class provides a single place to make all hardware definitions,
which can then be used in all experiments."""
from artiq.experiment import kernel

# Add the project root to the PYTHONPATH
import sys
from pathlib import Path
root_path=str(Path(__file__).resolve().parent.parent.parent)
sys.path.append(root_path)
sys.path.append(root_path+'/acf/')

from utils import get_config_dir
import json

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QSpinBox, QDoubleSpinBox,  QGridLayout
)
from PyQt5.QtCore import Qt
import sys

from artiq.applets.simple import TitleApplet, SimpleApplet

from acf.applets.control_panel import _control_panel

class DCControlWidget(_control_panel):
    def __init__(self, name, channel, parent=None):
        super().__init__(parent)

        #init parameters
        self.name=name
        self.channel=channel
        
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        
        # Channel label
        channel_label = QLabel(f"{self.name}")
        layout.addWidget(channel_label)
        
        # Frequency input
        vol_layout = QHBoxLayout()
        vol_label = QLabel("V: ")
        self.vol_input = QDoubleSpinBox()
        self.vol_input.setRange(-10, 10) 
        self.vol_input.setDecimals(3)
        vol_layout.addWidget(vol_label)
        vol_layout.addWidget(self.vol_input)
        layout.addLayout(vol_layout)
        
        # Control buttons
        btn_layout = QHBoxLayout()
        set_button = QPushButton("Set")
        btn_layout.addWidget(set_button)
        layout.addLayout(btn_layout)

        # Connect buttons to functions
        set_button.clicked.connect(self.set_channel)
        
        # Set main layout
        self.setLayout(layout)

    # def update_frequency(self):

    
    def set_channel(self):
        voltage = self.vol_input.value()
        self.dac_set(self.channel, voltage)
        # Here you would add the code to set the frequency and attenuation for the channel
        print(f"Setting DAC {self.name} - Voltage: {voltage} V")


class DCControlPanel(QWidget):
    def __init__(self, args, req):
        super().__init__()

        """Create a HardwareSetup instance for a given hardware setup. """
        self.hardware = []
        self.init_from_file()

        self.num_channels_per_row=8
        self.num_rows=int(len(self.hardware)//self.num_channels_per_row)

        if self.num_rows*self.num_channels_per_row<len(self.hardware): self.num_rows+=1

        self.init_ui()

        self.setWindowTitle('DC Control Panel')
        self.resize(900, 600)


    #functions for reading hardware stuff
    def init_from_file(self):
        for i in range(32):
            self.add_dc(f"channel {i}")
    def add_dc(self, name,):
        """Add a dds type device.

        Args:
            name (str): The name of the device.
            board_num (int): Which DDS board the device is on.
            channel (int): Which channel on the DDS board the device is on.
        """

        self.hardware.append({
            "name": name,
            "type": "dc",
        })
    

    def init_ui(self):
        layout = QGridLayout()
        channel_number = 0
        
        for row in range(self.num_rows):
            for col in range(self.num_channels_per_row):
                if channel_number >= len(self.hardware):
                    break
                dc_control = DCControlWidget(self.hardware[channel_number]['name'], channel_number)
                layout.addWidget(dc_control, row, col)
                channel_number += 1
        
        self.setLayout(layout)
    
    def data_changed(self, value, metadata, persist, mods):
        pass



def main():
    applet = SimpleApplet(DCControlPanel)
    applet.run()

if __name__ == "__main__":
    main()
