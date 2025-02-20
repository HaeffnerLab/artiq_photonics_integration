from artiq.experiment import kernel

# Add the project root to the PYTHONPATH
import sys
from pathlib import Path
root_path=str(Path(__file__).resolve().parent.parent.parent)
sys.path.append(root_path)
sys.path.append(root_path+'/acf/')
from acf.applets.control_panel import _control_panel

from PyQt5.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout,
    QDoubleSpinBox, QPushButton, QFrame, QSpacerItem, QSizePolicy
)
from PyQt5.QtCore import Qt
from artiq.applets.simple import SimpleApplet

import numpy as np
# ---------------------------
# Electrode Widget (Box with Border)
# ---------------------------

class ElectrodeWidget(QFrame):
    def __init__(self, electrode_index, set_voltage_callback, is_center=False):
        """
        electrode_index: Integer index for the electrode.
        set_voltage_callback: Function to call when "Submit" is pressed.
        is_center: If True, the electrode is labeled "Center Electrode".
        """
        super().__init__()
        self.electrode_index = electrode_index
        self.set_voltage_callback = set_voltage_callback
        self.grounded = False

        # Set a bordered look.
        self.setFrameStyle(QFrame.Box | QFrame.Raised)
        self.setLineWidth(2)
        self.setMidLineWidth(1)
        self.setStyleSheet("""
            QFrame {
                background-color: #f0f0f0;
                border: 2px solid #444;
                border-radius: 8px;
            }
        """)

        # Create the layout for this electrode.
        layout = QVBoxLayout()
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # Label: "Center Electrode" if flagged, otherwise "Elec N".
        label_text = "Center Electrode" if is_center else f"Elec {electrode_index}"
        self.label = QLabel(label_text)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("font-size: 10px;")
        layout.addWidget(self.label)

        # Large voltage input.
        self.voltage_spin = QDoubleSpinBox()
        # self.voltage_spin.setRange(-100.0, 100.0)
        self.voltage_spin.setRange(-10.0, 10.0)
        self.voltage_spin.setDecimals(3)
        self.voltage_spin.setValue(0.0)
        self.voltage_spin.setStyleSheet("font-size: 16px; padding: 4px;")
        self.voltage_spin.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.voltage_spin)

        # Button row: GND toggle and Submit.
        button_layout = QHBoxLayout()
        self.gnd_button = QPushButton("GND")
        self.gnd_button.setCheckable(True)
        self.gnd_button.clicked.connect(self.toggle_ground)
        button_layout.addWidget(self.gnd_button)
        self.submit_button = QPushButton("Submit")
        self.submit_button.clicked.connect(self.submit_voltage)
        button_layout.addWidget(self.submit_button)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def toggle_ground(self):
        """Toggle the electrode's GND state. When toggled, force voltage to 0 and disable editing."""
        self.grounded = self.gnd_button.isChecked()
        if self.grounded:
            self.voltage_spin.setValue(0.0)
            self.voltage_spin.setEnabled(False)
        else:
            self.voltage_spin.setEnabled(True)

    def submit_voltage(self):
        """Submit this electrode's voltage via the callback.
        If the electrode is GND toggled, 0 is submitted."""
        voltage = 0.0 if self.grounded else self.voltage_spin.value()
        self.set_voltage_callback(self.electrode_index, voltage)
        # (Optionally, update the spin box display.)
        self.voltage_spin.setValue(voltage)

# ---------------------------
# Electrode Grid (Left Panel)
# ---------------------------

class ElectrodeGrid(QWidget):
    def __init__(self, set_voltage_callback):
        """
        set_voltage_callback: Function called when any electrode's "Submit" is pressed.
        """
        super().__init__()
        # We'll create a vertical layout with three rows.
        main_layout = QVBoxLayout()
        main_layout.setSpacing(12)

        # Top row: 10 electrodes (indices 0-9).
        top_row = QHBoxLayout()
        top_row.setSpacing(12)
        self.top_electrodes = []
        for i in range(10):
            elec = ElectrodeWidget(i, set_voltage_callback)
            self.top_electrodes.append(elec)
            top_row.addWidget(elec)
        main_layout.addLayout(top_row)

        # Middle row: Only the center electrode (index 10), centered.
        middle_row = QHBoxLayout()
        self.center_electrode = ElectrodeWidget(10, set_voltage_callback, is_center=True)
        # Ensure it can expand horizontally:
        self.center_electrode.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        # Add the widget without additional stretches:
        middle_row.addWidget(self.center_electrode)
        main_layout.addLayout(middle_row)

        # Bottom row: 10 electrodes (indices 11-20).
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(12)
        self.bottom_electrodes = []
        for i in range(11, 21):
            elec = ElectrodeWidget(i, set_voltage_callback)
            self.bottom_electrodes.append(elec)
            bottom_row.addWidget(elec)
        main_layout.addLayout(bottom_row)

        self.setLayout(main_layout)

    def get_all_electrodes(self):
        """Return a list of all electrode widgets."""
        return self.top_electrodes + [self.center_electrode] + self.bottom_electrodes

# ---------------------------
# Multipole Input Panel (Right Panel)
# ---------------------------

class MultipoleInput(QWidget):
    def __init__(self, apply_multipole_callback, multipoles):
        """
        apply_multipole_callback: Function called with a list of 10 multipole voltages.
        """
        super().__init__()
        self.apply_multipole_callback = apply_multipole_callback
        layout = QVBoxLayout()
        layout.setSpacing(8)

        self.multipole_fields = []
        # Create 10 multipole input fields.
        for i in range(len(multipoles)):
            label = QLabel(f"{multipoles[i]}")
            layout.addWidget(label)
            spin = QDoubleSpinBox()
            # spin.setRange(-100.0, 100.0)
            spin.setRange(-10.0, 10.0)
            spin.setDecimals(3)
            spin.setValue(0.0)
            spin.setStyleSheet("font-size: 14px; padding: 2px;")
            spin.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            layout.addWidget(spin)
            self.multipole_fields.append(spin)

        # Submit button.
        submit_button = QPushButton("Submit Multipoles")
        submit_button.clicked.connect(self.submit_multipoles)
        layout.addWidget(submit_button)

        # Spacer to push items upward.
        layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
        self.setLayout(layout)

    def submit_multipoles(self):
        multipole_values = [spin.value() for spin in self.multipole_fields]
        self.apply_multipole_callback(multipole_values)

# ---------------------------
# Main Widget
# ---------------------------


# --- Settings ----
multipoles = ['Ex','Ey','Ez','U1','U2','U3','U4','U5']
threashold = 10
electrode_to_channel = {
    0: 0,
    1: 1,
    2: 2,
    3: 3,
    4: 4,
    5: 5,
    6: 6,
    7: 7,
    8: 8,
    9: 9,
    10: 10,
    11: 11,
    12: 12,
    13: 13,
    14: 14,
    15: 15,
    16: 16,
    17: 17,
    18: 18,
    19: 19,
    20: 20,
    21: 21

}
multipole_matrix = np.array([[-7.23383059e-01,  1.86301820e+00, -2.85486169e+00,
        -1.23375234e-01,  2.75303363e-01,  3.11410190e-04,
        -8.02809599e-02, -1.82120644e-01],
       [-7.24922370e-01,  1.85474591e+00,  2.65610470e+00,
        -1.22592722e-01,  2.77594757e-01,  1.23409756e-04,
         1.40348748e-01, -1.82191007e-01],
       [-8.33047518e-01, -5.20202754e-01, -4.65450401e-02,
         6.19107261e-02,  1.81891333e-03,  1.92836245e-04,
        -3.47806928e-04,  1.20770997e-01],
       [-2.88305789e+00, -2.66826827e+00, -1.58106180e-01,
         3.14131836e-01,  5.44462727e-03,  6.93647002e-04,
         4.30205616e-03,  3.76810386e-01],
       [-5.48623987e+00, -4.43638865e+00, -2.86501687e-01,
         5.67244848e-01,  1.25671722e-02,  1.62018569e-03,
         6.33821377e-02, -4.03378458e-01],
       [-4.63533767e+00, -3.07242571e+00, -2.33013405e-01,
         4.26202415e-01,  2.02366318e-02,  1.52045503e-03,
         8.21531240e-02, -9.28370320e-01],
       [-1.38918608e+00, -6.51067046e-01, -6.28836920e-02,
         9.72111966e-02,  6.52871742e-03,  4.50186605e-04,
         2.43751883e-02, -2.76017711e-01],
       [ 6.36689807e-01, -5.55005828e-01, -5.05542420e-02,
         7.14767943e-02,  8.30435775e-04, -1.06077494e-04,
         6.45565677e-03, -1.74329400e-01],
       [ 1.96780969e+00, -2.76134832e+00, -1.68576690e-01,
         3.43222717e-01,  2.02934775e-03, -2.93133658e-04,
         2.69725621e-02, -6.01659275e-01],
       [ 4.24632519e+00, -3.95180032e+00,  1.04096446e-01,
         4.39684654e-01, -1.48771048e-02, -1.06930396e-03,
        -1.36038848e-02,  9.68650132e-02],
       [ 3.90376446e+00, -2.32187794e+00,  3.15665634e-01,
         2.22757860e-01, -1.41392874e-02, -1.19110482e-03,
        -4.62465554e-02,  7.35293893e-01],
       [ 1.19239509e+00, -4.20388609e-01,  1.02042393e-01,
         3.52576597e-02, -3.90789551e-03, -3.69220552e-04,
        -1.44785952e-02,  2.26658219e-01],
       [-2.56243664e+00,  7.15524334e-01, -3.73815935e-01,
        -1.84967192e-01, -4.29687757e-02,  4.80571128e-04,
         1.05831023e-01,  7.16151897e-01],
       [-1.30815979e+00,  1.05044726e+00,  5.26492741e-01,
        -2.68496778e-01, -7.87730813e-02,  4.08291781e-04,
        -1.71483888e-01, -3.34561506e-01],
       [ 1.24752730e+00,  3.53946256e-01, -5.48622122e-01,
        -8.46647819e-02, -3.62553459e-02, -2.30884707e-05,
         1.73788854e-01, -1.04927364e+00],
       [-7.99846105e-01,  2.77481922e+00, -1.20670011e-01,
        -1.87678421e-01, -1.38638207e-01, -3.09407019e-03,
         3.22429021e-02, -2.00920810e-01],
       [-7.83242038e-01,  2.77100282e+00, -1.22209641e-01,
        -1.86770630e-01, -1.38393855e-01,  3.51268091e-03,
         3.28108708e-02, -2.04283231e-01]])
# -----------------

class MainWidget(_control_panel):
    def __init__(self, args, req):
        super().__init__()
        self.setWindowTitle("Electrode Voltage Control")

        # Main layout: left (electrodes) and right (multipole inputs).
        main_layout = QHBoxLayout()
        # Left panel: the custom electrode grid.
        self.electrode_grid = ElectrodeGrid(self.set_voltage)
        main_layout.addWidget(self.electrode_grid, 8)  # ~80% width
        # Right panel: multipole inputs.
        self.multipole_input = MultipoleInput(self.apply_multipole_voltages, multipoles)
        main_layout.addWidget(self.multipole_input, 2)  # ~20% width
        self.setLayout(main_layout)

    def set_voltage(self, electrode_index, voltage):
        """
        Placeholder function to set the voltage on a given electrode.
        Replace the print() with your hardware-control routine.
        """
        channel = electrode_to_channel[electrode_index]
        self.dac_set(channel, voltage)
        print(f"Setting voltage for Electrode {electrode_index} to {voltage:.3f} at channel {channel}")

    def apply_multipole_voltages(self, multipole_values):
        """
        Applies multipole voltage settings:
          - For each electrode that is not GND, set voltage = multipole_values[electrode_index % 10].
          - For electrodes marked GND, set voltage to 0.
        """
        voltages = multipole_matrix @ multipole_values

        if max(voltages) > threashold or min(voltages) < -threashold:
            print(f"Caclulated voltage(s) outside threashold: {voltages}. Nothing done.")
            return
        
        electrodes = self.electrode_grid.get_all_electrodes()

        electrodes_active = 0
        for elec in electrodes:
            if not elec.grounded:
                electrodes_active += 1

        if electrodes_active != len(voltages):
            print(f"{electrodes_active} electrodes active but {len(voltages)} voltages calculated. Nothing done")
            return
        
        set_channels = [i for i in range(32)]
        set_voltages = [0.0 for _ in range(32)]
        
        voltage_index = 0
        for elec in electrodes:
            if elec.grounded:
                new_voltage = 0.0
            else:
                new_voltage = voltages[voltage_index]
                voltage_index += 1
            set_voltages[electrode_to_channel[elec.electrode_index]] = new_voltage
            elec.voltage_spin.setValue(new_voltage)
        
        self.dac_set_mul(set_channels, set_voltages)
        print([f"{set_channels[i]} : {set_voltages[i]}"  for i in range(32)])

    def data_changed(self, value, metadata, persist, mods):
        pass


# ---------------------------
# Main Entry Point using SimpleApplet
# ---------------------------

def main():
    applet = SimpleApplet(MainWidget)
    applet.run()

if __name__ == "__main__":
    main()