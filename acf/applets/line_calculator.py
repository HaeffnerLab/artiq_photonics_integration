"""
Line Calculator applet for ARTIQ.
This module provides a visualization tool for calculating and displaying Zeeman energy levels
and transitions in atomic systems.
"""

import sys
import random
from typing import List, Tuple, Dict, Any
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton
import pyqtgraph as pg
import numpy as np
from artiq.applets.simple import TitleApplet, SimpleApplet
from pyqtgraph.Qt import QtGui

# Physical constants
muB = 9.274009995e-24  # Bohr magneton
h = 6.62607015e-34     # Planck's constant
hbar = h / (2 * np.pi) # Reduced Planck's constant

def Zeeman_Enrg(B: float, mS: float, mD: float, gS: float, gD: float, linecentre: float) -> float:
    """
    Calculate Zeeman energy for given parameters.
    
    Args:
        B: Magnetic field in Gauss
        mS: Magnetic quantum number for S state
        mD: Magnetic quantum number for D state
        gS: g-factor for S state
        gD: g-factor for D state
        linecentre: Center frequency in MHz (without 2pi)
        
    Returns:
        float: Energy in MHz
    """
    freq1 = B * gS * mS * muB / (h * 1e6)
    freq2 = B * gD * mD * muB / (h * 1e6)
    return linecentre + freq2 - freq1

def Solve_B(mS1: float, mD1: float, mS2: float, mD2: float, 
           gS: float, gD: float, freq_1: float, freq_2: float) -> Tuple[float, float]:
    """
    Solve for magnetic field and line center from two frequencies.
    
    Args:
        mS1, mD1: Magnetic quantum numbers for first transition
        mS2, mD2: Magnetic quantum numbers for second transition
        gS, gD: g-factors for S and D states
        freq_1, freq_2: Frequencies in MHz
        
    Returns:
        Tuple[float, float]: (B_field in Gauss, linecenter in MHz)
    """
    B_field = (freq_1 - freq_2) / (
        gD * mD1 * muB / (h * 1e6) - gS * mS1 * muB / (h * 1e6) - 
        gD * mD2 * muB / (h * 1e6) + gS * mS2 * muB / (h * 1e6)
    )
    
    linecenter = freq_1 - B_field * (gD * mD1 * muB / (h * 1e6) - gS * mS1 * muB / (h * 1e6))
    
    return B_field, linecenter

class LineCalculator(QWidget):
    """
    A widget for calculating and displaying Zeeman energy levels and transitions.
    """
    
    def __init__(self, args: Any, req: Any) -> None:
        """
        Initialize the LineCalculator widget.
        
        Args:
            args: Command line arguments
            req: Request object from ARTIQ
        """
        super().__init__()
        self.req = req
        
        # Define line pairs (S, D) for transitions
        self.line_pairs = [
            # S, D
            (-1/2, 3/2),   # S-1/2 -> D3/2
            (-1/2, 1/2),   # S-1/2 -> D1/2
            (-1/2, -1/2),  # S-1/2 -> D-1/2
            (-1/2, -3/2),  # S-1/2 -> D-3/2
            (-1/2, -5/2),  # S-1/2 -> D-5/2
            
            (1/2, -3/2),   # S1/2 -> D-3/2
            (1/2, -1/2),   # S1/2 -> D-1/2
            (1/2, 1/2),    # S1/2 -> D1/2
            (1/2, 3/2),    # S1/2 -> D3/2
            (1/2, 5/2),    # S1/2 -> D5/2
            (0, 0)         # Center
        ]

        # Labels for each transition
        self.line_labels = [
            'S-1/2 D3/2', 'S-1/2 D1/2', 'S-1/2 D-1/2', 'S-1/2 D-3/2', 'S-1/2 D-5/2',
            'S1/2 D-3/2', 'S1/2 D-1/2', 'S1/2 D1/2', 'S1/2 D3/2', 'S1/2 D5/2',
            'center'
        ]

        # g-factors for different states
        self.g_factor = {
            'S1_2': 2.0,
            'D5_2': 6/5.0
        }

        # Initialize state variables
        self.lines = []
        self.B = 0  # in Gauss
        self.linecenter = 0  # in MHz
        self.line_freq = [0] * len(self.line_labels)

        # Validate required arguments
        if args.Sm1_2_Dm5_2 is None:
            raise RuntimeError("S -1/2 -> D -5/2 line missing")
        if args.Sm1_2_Dm1_2 is None:
            raise RuntimeError("S -1/2 -> D -1/2 line missing")

        self.args = args
        self.calculate_all_lines()
        self.initUI()

    def calculate_all_lines(self) -> None:
        """Calculate frequencies for all transitions."""
        for i, (mS, mD) in enumerate(self.line_pairs):
            self.line_freq[i] = Zeeman_Enrg(
                self.B, mS, mD, 
                self.g_factor['S1_2'], self.g_factor['D5_2'], 
                self.linecenter
            )

    def data_changed(self, value: Dict[str, float], 
                    metadata: Dict[str, Any], 
                    persist: Dict[str, Any], 
                    mod_buffer: Dict[str, Any]) -> None:
        """
        Handle data updates from the experiment.
        
        Args:
            value: Dictionary containing the latest dataset values
            metadata: Dictionary containing metadata about the datasets
            persist: Dictionary for persistent data
            mod_buffer: Dictionary containing modified buffer data
        """
        # Update line parameters
        self.Sm1_2_Dm1_2 = value[self.args.Sm1_2_Dm1_2] / 1e6 * 2
        self.Sm1_2_Dm5_2 = value[self.args.Sm1_2_Dm5_2] / 1e6 * 2

        # Calculate B field and line center
        self.B, self.linecenter = Solve_B(
            -1/2., -1/2., -1/2., -5/2.,
            self.g_factor['S1_2'], self.g_factor['D5_2'],
            self.Sm1_2_Dm1_2, self.Sm1_2_Dm5_2
        )
        
        self.calculate_all_lines()
        self.update_lines()

        # Update datasets
        self.req.set_dataset('__param__qubit/B', self.B * 10000)
        self.req.set_dataset('__param__qubit/center', self.line_freq[10]/2 * 1e6, unit='MHz', persist=True)
        self.req.set_dataset('__param__qubit/S1_2_Dm3_2', self.line_freq[5]/2 * 1e6, unit='MHz', persist=True)
        self.req.set_dataset('__param__qubit/Sm1_2_D3_2', self.line_freq[0]/2 * 1e6, unit='MHz', persist=True)
        self.req.set_dataset('__param__qubit/Sm1_2_S1_2', 
                           np.abs(self.B * self.g_factor['S1_2'] * muB / h), 
                           unit='MHz', persist=True)

    def initUI(self) -> None:
        """Initialize the user interface."""
        layout = QVBoxLayout()
        
        # Create plot widget
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setRange(yRange=(0, 1), xRange=(230, 240))
        layout.addWidget(self.plot_widget)

        # Initialize text items
        self.text_items_top = []
        self.text_items_bottom = []
        
        # Create lines and labels
        for i, label in enumerate(self.line_labels):
            x = self.line_freq[i]/2
            line = self.plot_widget.plot([x, x], [0, 1], pen='r')

            # Create text items
            text_top = pg.TextItem(text=f'{self.line_freq[i]:.5f}', anchor=(0.5, -1.5))
            text_bottom = pg.TextItem(text=label, anchor=(0.5, 1.5))

            # Position text items
            text_top.setPos(x, 1)
            text_bottom.setPos(x, 0)

            # Add items to plot
            self.plot_widget.addItem(text_top)
            self.plot_widget.addItem(text_bottom)
            
            # Store items
            self.lines.append(line)
            self.text_items_top.append(text_top)
            self.text_items_bottom.append(text_bottom)

        # Set up axis labels
        self.x_label = pg.LabelItem(justify='center')
        self.x_label.setText("X Axis: $\\alpha$")
        self.plot_widget.getPlotItem().setLabel('bottom', text='MHz')
        
        # Set layout and window properties
        self.setLayout(layout)
        self.setGeometry(100, 100, 800, 600)

    def update_lines(self) -> None:
        """Update the positions of all lines and labels."""
        self.calculate_all_lines()

        for i, (line, text_top, text_bottom) in enumerate(zip(self.lines, self.text_items_top, self.text_items_bottom)):
            x = self.line_freq[i]/2
            line.setData([x, x], [0, 1])
            text_top.setPos(x, 1)
            text_bottom.setPos(x, 0)
            text_top.setText(f'{x:.5f}')
            text_bottom.setText(self.line_labels[i])

def main() -> None:
    """Set up and run the line calculator applet."""
    applet = SimpleApplet(LineCalculator)
    
    # Add required datasets
    applet.add_dataset("Sm1_2_Dm5_2", "Sm1_2_Dm5_2 line")
    applet.add_dataset("Sm1_2_Dm1_2", "Sm1_2_Dm1_2 line")

    applet.run()

if __name__ == "__main__":
    main()