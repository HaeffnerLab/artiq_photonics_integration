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
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QLineEdit, QPushButton, QSpinBox, QDoubleSpinBox,  QGridLayout
)
from PyQt5.QtCore import Qt
import sys

from artiq.applets.simple import TitleApplet, SimpleApplet

from acf.applets.control_panel import _control_panel

class DDSControlWidget(_control_panel):
    def __init__(self, name, device_str, parent=None):
        super().__init__(parent)

        #init parameters
        self.name=name
        self.device_str=device_str
        
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        
        # Channel label
        channel_label = QLabel(f"{self.name}")
        layout.addWidget(channel_label)
        
        # Frequency input
        freq_layout = QHBoxLayout()
        freq_label = QLabel("Freq (MHz): ")
        self.freq_input = QDoubleSpinBox()
        self.freq_input.setRange(0, 300.0) 
        self.freq_input.setDecimals(5)
        freq_layout.addWidget(freq_label)
        freq_layout.addWidget(self.freq_input)
        layout.addLayout(freq_layout)
        
        # Attenuation input
        att_layout = QHBoxLayout()
        att_label = QLabel("Att (dB): ")
        self.att_input =  QDoubleSpinBox()
        self.att_input.setRange(0, 30) 
        self.att_input.setDecimals(5)
        att_layout.addWidget(att_label)
        att_layout.addWidget(self.att_input)
        layout.addLayout(att_layout)
        
        # Control buttons
        btn_layout = QHBoxLayout()
        set_button = QPushButton("Set")
        off_button = QPushButton("Off")
        btn_layout.addWidget(set_button)
        btn_layout.addWidget(off_button)
        layout.addLayout(btn_layout)

        # Connect buttons to functions
        set_button.clicked.connect(self.set_channel)
        off_button.clicked.connect(self.off_channel)
        
        # Set main layout
        self.setLayout(layout)

    # def update_frequency(self):

    
    def set_channel(self):
        frequency = self.freq_input.value()
        attenuation = self.att_input.value()
        # Here you would add the code to set the frequency and attenuation for the channel
        self.dds_set_frequency(self.device_str, frequency, attenuation)
        print(f"Setting DDS Channel {self.name} - Frequency: {frequency} MHz, Attenuation: {attenuation} dB")

    def off_channel(self):
        # Here you would add the code to turn off the channel
        self.dds_turn_off(self.device_str)
        print(f"Turning off DDS Channel {self.name}")

class DDSControlPanel(QWidget):
    def __init__(self, args, req):
        super().__init__()

        """Create a HardwareSetup instance for a given hardware setup. """
        self.hardware = []
        self.init_from_file()

        self.num_channels_per_row=4
        self.num_rows=int(len(self.hardware)//self.num_channels_per_row)

        if self.num_rows*self.num_channels_per_row<len(self.hardware): self.num_rows+=1

        # print(len(self.hardware), self.num_rows)
        self.init_ui()

        self.setWindowTitle('DDS Control Panel')
        self.resize(900, 600)


    #functions for reading hardware stuff
    def init_from_file(self):
        """Create the hardware definition from json file."""
        config_file = get_config_dir() / "hardware.json"

        with config_file.open() as fh:
            data = json.load(fh)

        for dds_device in data["dds"]:
            self.add_dds(dds_device["name"], dds_device["board"], dds_device["channel"])
    def add_dds(self, name, board_num, channel):
        """Add a dds type device.

        Args:
            name (str): The name of the device.
            board_num (int): Which DDS board the device is on.
            channel (int): Which channel on the DDS board the device is on.
        """
        if not name.isidentifier():
            raise RuntimeError(f"dds name '{name}' is not a valid python identifier.")

        self.hardware.append({
            "name": name,
            "type": "dds",
            "device_str": f"urukul{board_num}_ch{channel}"
        })
    

    def init_ui(self):
        layout = QGridLayout()
        channel_number = 0
        
        for row in range(self.num_rows):
            for col in range(self.num_channels_per_row):
                if channel_number >= len(self.hardware):
                    break
                dds_control = DDSControlWidget(self.hardware[channel_number]['name'], self.hardware[channel_number]['device_str'], self)
                layout.addWidget(dds_control, row, col)
                channel_number += 1
        
        self.setLayout(layout)
    
    def data_changed(self, value, metadata, persist, mods):
        pass



def main():
    applet = SimpleApplet(DDSControlPanel)
    applet.run()


if __name__ == "__main__":
    main()
