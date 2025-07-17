import numpy as np
import PyQt5
import pyqtgraph as pg
from PyQt5.QtGui import QColor
from PyQt5.QtCore import Qt
import os
import json
import glob
from datetime import datetime

from artiq.applets.simple import TitleApplet, SimpleApplet


import time
from collections import deque
# timestamp_ms = int(time.time() * 1000)
# print(timestamp_ms)

class Drift_Tracker(pg.PlotWidget):

    def __init__(self, args, req):
        pg.PlotWidget.__init__(self)
        self.args = args
        self.req = req

        self.time_now = time.time()
        self.freq_mode1_dataset_name = self.args.freq_mode1
        self.freq_mode2_dataset_name = self.args.freq_mode2
        self.freq_mode_single_ion_dataset_name = self.args.freq_mode_single_ion

        self.freq_mode1_var_dataset_name = self.args.freq_mode1_var
        self.freq_mode2_var_dataset_name = self.args.freq_mode2_var
        self.freq_mode_single_ion_var_dataset_name = self.args.freq_mode_single_ion_var

        # queues for saving the frequency data for each mode
        L = 100
        self.queue_freq_mode1 = deque(maxlen=L)
        self.queue_freq_mode2 = deque(maxlen=L)
        self.queue_freq_single_ion = deque(maxlen=L)
        
        # queues for saving the frequency error data for each mode
        self.queue_freq_mode1_var = deque(maxlen=L)
        self.queue_freq_mode2_var = deque(maxlen=L)
        self.queue_freq_single_ion_var = deque(maxlen=L)
        
        # Separate time queues for each mode
        self.queue_time_mode1 = deque(maxlen=L)
        self.queue_time_mode2 = deque(maxlen=L)
        self.queue_time_single_ion = deque(maxlen=L)
        
        # Store the initial frequency values
        self.initial_freq_mode1 = None
        self.initial_freq_mode2 = None
        self.initial_freq_single_ion = None

        self.if_initial_freq_mode1 = False
        self.if_initial_freq_mode2 = False
        self.if_initial_freq_single_ion = False
        
        # Store the last frequency values to check for updates
        self.last_freq_mode1 = None
        self.last_freq_mode2 = None
        self.last_freq_single_ion = None

        # Create a timestamp-based filename for saving data
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.data_dir = os.path.join(os.path.expanduser("~"), "drift_tracker_data")
        os.makedirs(self.data_dir, exist_ok=True)
        self.data_file = os.path.join(self.data_dir, f"drift_tracker_motion_{timestamp}.json")
        
        # Load previous data if available
        self.load_data()

        # Set tracking 'b' to the latest frequency for each mode
        if len(self.queue_freq_mode1) > 0:
            self.req.set_dataset('__param__tracker/mode1/a', 0)
            self.req.set_dataset('__param__tracker/mode1/b', self.queue_freq_mode1[-1])
        
        if len(self.queue_freq_mode2) > 0:
            self.req.set_dataset('__param__tracker/mode2/a', 0)
            self.req.set_dataset('__param__tracker/mode2/b', self.queue_freq_mode2[-1])
        
        if len(self.queue_freq_single_ion) > 0:
            self.req.set_dataset('__param__tracker/mode_single_ion/a', 0)
            self.req.set_dataset('__param__tracker/mode_single_ion/b', self.queue_freq_single_ion[-1])

        title = "Motion Frequency Drift Tracker"

        self.setLabel("bottom", 'time(s)')
        self.setLabel("left", 'frequency drift (MHz)')
        self.setTitle(title)
        self.setBackground('k')
        #.setBackground(QColor(240, 240, 240))
        
        self.waiting_for_size_update = False
    
    def load_data(self):
        try:
            # Get all drift tracker data files
            data_files = glob.glob(os.path.join(os.path.expanduser("~"), "drift_tracker_data", "drift_tracker_motion_*.json"))
            if not data_files:
                # Check old location for backward compatibility
                old_file = os.path.join(os.path.expanduser("~"), "drift_tracker_data.json")
                if os.path.exists(old_file):
                    data_files = [old_file]
            
            # Filter out data older than 3 hours
            current_time = time.time()
            three_hours_ago = current_time - 10800  # 3 hours in seconds
            
            for file_path in data_files:
                if os.path.exists(file_path):
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                    
                    # Load mode 1 data
                    if 'mode1' in data:
                        times = data['mode1'].get('times', [])
                        freqs = data['mode1'].get('freqs', [])
                        freq_vars = data['mode1'].get('freq_vars', [])
                        # Filter by time and add to queue
                        for i, (t, f) in enumerate(zip(times, freqs)):
                            if t > three_hours_ago and t not in self.queue_time_mode1:
                                self.queue_time_mode1.append(t)
                                self.queue_freq_mode1.append(f)
                                if i < len(freq_vars):
                                    self.queue_freq_mode1_var.append(freq_vars[i])
                                else:
                                    self.queue_freq_mode1_var.append(0)
                    
                    # Load mode 2 data
                    if 'mode2' in data:
                        times = data['mode2'].get('times', [])
                        freqs = data['mode2'].get('freqs', [])
                        freq_vars = data['mode2'].get('freq_vars', [])
                        # Filter by time and add to queue
                        for i, (t, f) in enumerate(zip(times, freqs)):
                            if t > three_hours_ago and t not in self.queue_time_mode2:
                                self.queue_time_mode2.append(t)
                                self.queue_freq_mode2.append(f)
                                if i < len(freq_vars):
                                    self.queue_freq_mode2_var.append(freq_vars[i])
                                else:
                                    self.queue_freq_mode2_var.append(0)
                    
                    # Load single ion mode data
                    if 'single_ion' in data:
                        times = data['single_ion'].get('times', [])
                        freqs = data['single_ion'].get('freqs', [])
                        freq_vars = data['single_ion'].get('freq_vars', [])
                        # Filter by time and add to queue
                        for i, (t, f) in enumerate(zip(times, freqs)):
                            if t > three_hours_ago and t not in self.queue_time_single_ion:
                                self.queue_time_single_ion.append(t)
                                self.queue_freq_single_ion.append(f)
                                if i < len(freq_vars):
                                    self.queue_freq_single_ion_var.append(freq_vars[i])
                                else:
                                    self.queue_freq_single_ion_var.append(0)
            
            # Sort the queues by time
            if self.queue_time_mode1:
                sorted_data = sorted(zip(self.queue_time_mode1, self.queue_freq_mode1, self.queue_freq_mode1_var))
                self.queue_time_mode1.clear()
                self.queue_freq_mode1.clear()
                self.queue_freq_mode1_var.clear()
                for t, f, v in sorted_data:
                    self.queue_time_mode1.append(t)
                    self.queue_freq_mode1.append(f)
                    self.queue_freq_mode1_var.append(v)
            
            if self.queue_time_mode2:
                sorted_data = sorted(zip(self.queue_time_mode2, self.queue_freq_mode2, self.queue_freq_mode2_var))
                self.queue_time_mode2.clear()
                self.queue_freq_mode2.clear()
                self.queue_freq_mode2_var.clear()
                for t, f, v in sorted_data:
                    self.queue_time_mode2.append(t)
                    self.queue_freq_mode2.append(f)
                    self.queue_freq_mode2_var.append(v)
            
            if self.queue_time_single_ion:
                sorted_data = sorted(zip(self.queue_time_single_ion, self.queue_freq_single_ion, self.queue_freq_single_ion_var))
                self.queue_time_single_ion.clear()
                self.queue_freq_single_ion.clear()
                self.queue_freq_single_ion_var.clear()
                for t, f, v in sorted_data:
                    self.queue_time_single_ion.append(t)
                    self.queue_freq_single_ion.append(f)
                    self.queue_freq_single_ion_var.append(v)
                
            print(f"Loaded drift tracker data from {len(data_files)} files")
        except Exception as e:
            print(f"Error loading drift tracker data: {e}")
    
    def save_data(self):
        try:
            data = {}
            
            # Save mode 1 data - store absolute frequencies
            if self.initial_freq_mode1 is not None:
                data['mode1'] = {
                    'initial_freq': self.initial_freq_mode1,
                    'times': list(self.queue_time_mode1),
                    'freqs': list(self.queue_freq_mode1),  # Already storing absolute frequencies
                    'freq_vars': list(self.queue_freq_mode1_var)
                }
            
            # Save mode 2 data - store absolute frequencies
            if self.initial_freq_mode2 is not None:
                data['mode2'] = {
                    'initial_freq': self.initial_freq_mode2,
                    'times': list(self.queue_time_mode2),
                    'freqs': list(self.queue_freq_mode2),  # Already storing absolute frequencies
                    'freq_vars': list(self.queue_freq_mode2_var)
                }
            
            # Save single ion mode data - store absolute frequencies
            if self.initial_freq_single_ion is not None:
                data['single_ion'] = {
                    'initial_freq': self.initial_freq_single_ion,
                    'times': list(self.queue_time_single_ion),
                    'freqs': list(self.queue_freq_single_ion),  # Already storing absolute frequencies
                    'freq_vars': list(self.queue_freq_single_ion_var)
                }
            
            with open(self.data_file, 'w') as f:
                json.dump(data, f)
            
            print(f"Saved drift tracker data to {self.data_file}")
        except Exception as e:
            print(f"Error saving drift tracker data: {e}")
    
    def fit_quadratic(self, t, f):
        # Fit quadratic curve (degree 2 polynomial)
        coeffs = np.polyfit(t, f, 2)  # Returns [a, b, c]
        return coeffs[0], coeffs[1], coeffs[2]  # Extract a, b, c

    def fit_linear(self, t, f, weights=None):
        # Fit linear curve (degree 1 polynomial) with optional weights
        coeffs = np.polyfit(t, f, 1, w=weights)  # Returns [a, b]
        return coeffs[0], coeffs[1]  # Extract a, b
    
    
    def data_changed(self, value, metadata, persist, mod_buffer):
        
        # Get the new frequencies for each mode
        freq_mode1 = value.get(self.freq_mode1_dataset_name, None)
        freq_mode2 = value.get(self.freq_mode2_dataset_name, None)
        freq_single_ion = value.get(self.freq_mode_single_ion_dataset_name, None)

        # Get the new frequency errors for each mode
        freq_mode1_var = value.get(self.freq_mode1_var_dataset_name, None)
        freq_mode2_var = value.get(self.freq_mode2_var_dataset_name, None)
        freq_single_ion_var = value.get(self.freq_mode_single_ion_var_dataset_name, None)

        current_time = time.time()
        updated = False
        
        # Process mode 1 data
        if freq_mode1 is not None:
            # Initialize reference value if not set yet
            if not self.if_initial_freq_mode1:
                self.initial_freq_mode1 = freq_mode1
                self.last_freq_mode1 = freq_mode1
                self.if_initial_freq_mode1 = True
                updated = True
                
            # Only append if the frequency value has changed
            if freq_mode1 != self.last_freq_mode1:
                self.queue_freq_mode1.append(freq_mode1)  # Store absolute frequency
                self.queue_time_mode1.append(current_time)
                self.queue_freq_mode1_var.append(freq_mode1_var if freq_mode1_var is not None else 0)
                self.last_freq_mode1 = freq_mode1
                updated = True
        
        # Process mode 2 data
        if freq_mode2 is not None:
            # Initialize reference value if not set yet
            if not self.if_initial_freq_mode2:
                self.initial_freq_mode2 = freq_mode2
                self.last_freq_mode2 = freq_mode2
                self.if_initial_freq_mode2 = True
                updated = True
                
            # Only append if the frequency value has changed
            if freq_mode2 != self.last_freq_mode2:
                self.queue_freq_mode2.append(freq_mode2)  # Store absolute frequency
                self.queue_time_mode2.append(current_time)
                self.queue_freq_mode2_var.append(freq_mode2_var if freq_mode2_var is not None else 0)
                self.last_freq_mode2 = freq_mode2
                updated = True
        
        # Process single ion mode data
        if freq_single_ion is not None:
            # Initialize reference value if not set yet
            if not self.if_initial_freq_single_ion:
                self.initial_freq_single_ion = freq_single_ion
                self.last_freq_single_ion = freq_single_ion
                self.if_initial_freq_single_ion = True
                updated = True
                
            # Only append if the frequency value has changed
            if freq_single_ion != self.last_freq_single_ion:
                self.queue_freq_single_ion.append(freq_single_ion)  # Store absolute frequency
                self.queue_time_single_ion.append(current_time)
                self.queue_freq_single_ion_var.append(freq_single_ion_var if freq_single_ion_var is not None else 0)
                self.last_freq_single_ion = freq_single_ion
                updated = True
        
        # Save data when updated
        if updated:
            self.save_data()
        
        # Only update the plot if at least one frequency value has changed
        if updated:
            # Clear the plot and add a legend
            self.clear()
            self.addLegend()
            
            # Plot mode 1 drift (red)
            if self.initial_freq_mode1 is not None and len(self.queue_freq_mode1) > 0:
                # Calculate drift for plotting
                drift_values = np.array(self.queue_freq_mode1) - self.initial_freq_mode1
                error_values = np.array(self.queue_freq_mode1_var)
                time_values = np.array(self.queue_time_mode1) - self.time_now
                
                # Create error bar item with proper parameters
                error_item = pg.ErrorBarItem(
                    x=time_values,
                    y=drift_values,
                    height=error_values,  # Use error_values directly for standard deviation
                    pen=pg.mkPen(color=(255, 0, 0), width=2),
                    beam=0.5  # width of the error bar caps
                )
                self.addItem(error_item)
                
                plot_mode1 = self.plot(
                    time_values,
                    drift_values,
                    symbol="o", 
                    name=f'Mode 1 (ref: {self.initial_freq_mode1:.3f} MHz)',
                    pen=None,  # Remove line connecting points to make error bars more visible
                    symbolBrush=(255, 0, 0),  # Red
                    symbolPen=pg.mkPen(color=(255, 0, 0), width=1),
                    symbolSize=8
                )
            
            # Plot mode 2 drift (green)
            if self.initial_freq_mode2 is not None and len(self.queue_freq_mode2) > 0:
                # Calculate drift for plotting
                drift_values = np.array(self.queue_freq_mode2) - self.initial_freq_mode2
                error_values = np.array(self.queue_freq_mode2_var)
                time_values = np.array(self.queue_time_mode2) - self.time_now
                
                # Create error bar item with proper parameters
                error_item = pg.ErrorBarItem(
                    x=time_values,
                    y=drift_values,
                    height=error_values,  # Use error_values directly for standard deviation
                    pen=pg.mkPen(color=(0, 255, 0), width=2),
                    beam=0.5  # width of the error bar caps
                )
                self.addItem(error_item)
                
                plot_mode2 = self.plot(
                    time_values,
                    drift_values,
                    symbol="o", 
                    name=f'Mode 2 (ref: {self.initial_freq_mode2:.3f} MHz)',
                    pen=None,  # Remove line connecting points to make error bars more visible
                    symbolBrush=(0, 255, 0),  # Green
                    symbolPen=pg.mkPen(color=(0, 255, 0), width=1),
                    symbolSize=8
                )
            
            # Plot single ion mode drift (blue)
            if self.initial_freq_single_ion is not None and len(self.queue_freq_single_ion) > 0:
                # Calculate drift for plotting
                drift_values = np.array(self.queue_freq_single_ion) - self.initial_freq_single_ion
                error_values = np.array(self.queue_freq_single_ion_var)
                time_values = np.array(self.queue_time_single_ion) - self.time_now
                
                # Create error bar item with proper parameters
                error_item = pg.ErrorBarItem(
                    x=time_values,
                    y=drift_values,
                    height=error_values,  # Use error_values directly for standard deviation
                    pen=pg.mkPen(color=(0, 0, 255), width=2),
                    beam=0.5  # width of the error bar caps
                )
                self.addItem(error_item)
                
                plot_single_ion = self.plot(
                    time_values,
                    drift_values,
                    symbol="o", 
                    name=f'Single Ion (ref: {self.initial_freq_single_ion:.3f} MHz)',
                    pen=None,  # Remove line connecting points to make error bars more visible
                    symbolBrush=(0, 0, 255),  # Blue
                    symbolPen=pg.mkPen(color=(0, 0, 255), width=1),
                    symbolSize=8
                )


        #################################
        # Fit quadratic curves for each mode if we have enough recent data points
        current_time = time.time()
        two_hours_ago = current_time - 7200/2# 7200 seconds = 2 hours

        num_points=5
        num_points_threshold=30
        
        # Mode 1 fitting
        if self.initial_freq_mode1 is not None and len(self.queue_freq_mode1) > 0:
            # Get indices of points within last 2 hours
            recent_indices = [i for i, t in enumerate(self.queue_time_mode1) if t > two_hours_ago]
            
            # Get recent points
            if len(recent_indices) > num_points_threshold:
                recent_times = np.array(self.queue_time_mode1)[recent_indices]
                # Calculate drift for fitting
                recent_freqs = np.array(self.queue_freq_mode1)[recent_indices] - self.initial_freq_mode1
                recent_errors = np.array(self.queue_freq_mode1_var)[recent_indices]

                recent_freqs=recent_freqs[-num_points:]
                recent_times=recent_times[-num_points:]
                recent_errors=recent_errors[-num_points:]
                
                # Calculate weights from errors (inverse variance weighting)
                # Avoid division by zero by adding small epsilon
                epsilon = 1e-10
                weights = 1.0 / (recent_errors + epsilon)
                
                # Fit with at+b using weighted least squares
                try:
                    a1, b1 = self.fit_linear(recent_times, recent_freqs, weights=weights)
                    # Store coefficients in dataset
                    self.req.set_dataset('__param__tracker/mode1/a', a1)
                    self.req.set_dataset('__param__tracker/mode1/b', b1+self.initial_freq_mode1)
                except Exception as e:
                    print(f"Error fitting mode 1: {e}")
                    a1=0
                    b1=recent_freqs[-1]
                    self.req.set_dataset('__param__tracker/mode1/a', 0)
                    self.req.set_dataset('__param__tracker/mode1/b', recent_freqs[-1]+self.initial_freq_mode1)

                # Plot the fit
                fit_times = np.array(self.queue_time_mode1)
                fit_values = a1*fit_times + b1
                self.plot(fit_times - self.time_now, fit_values, 
                          pen=pg.mkPen(color=(255, 100, 100), width=2, style=Qt.DashLine), 
                          name='Mode 1 fit')
            else:
                self.req.set_dataset('__param__tracker/mode1/a', 0)
                self.req.set_dataset('__param__tracker/mode1/b', self.queue_freq_mode1[-1])
                
        elif len(self.queue_freq_mode1) > 0:
            # Not enough points for fitting, set a=b=0, c=current frequency
            self.req.set_dataset('__param__tracker/mode1/a', 0)
            self.req.set_dataset('__param__tracker/mode1/b', self.queue_freq_mode1[-1])
        
        # Mode 2 fitting
        if self.initial_freq_mode2 is not None and len(self.queue_freq_mode2) > 0:
            # Get indices of points within last 2 hours
            recent_indices = [i for i, t in enumerate(self.queue_time_mode2) if t > two_hours_ago]
            
            # Get recent points
            if len(recent_indices) > num_points_threshold:
                recent_times = np.array(self.queue_time_mode2)[recent_indices]
                # Calculate drift for fitting
                recent_freqs = np.array(self.queue_freq_mode2)[recent_indices] - self.initial_freq_mode2
                recent_errors = np.array(self.queue_freq_mode2_var)[recent_indices]

                recent_freqs=recent_freqs[-num_points:]
                recent_times=recent_times[-num_points:]
                recent_errors=recent_errors[-num_points:]
                
                # Calculate weights from errors (inverse variance weighting)
                # Avoid division by zero by adding small epsilon
                epsilon = 1e-10
                weights = 1.0 / (recent_errors + epsilon)

                try:
                    a2, b2 = self.fit_linear(recent_times, recent_freqs, weights=weights)
                    # Store coefficients in dataset
                    self.req.set_dataset('__param__tracker/mode2/a', a2)
                    self.req.set_dataset('__param__tracker/mode2/b', b2+self.initial_freq_mode2)
                except Exception as e:
                    print(f"Error fitting mode 2: {e}")
                    a2=0
                    b2=recent_freqs[-1]
                    self.req.set_dataset('__param__tracker/mode2/a', 0)
                    self.req.set_dataset('__param__tracker/mode2/b', recent_freqs[-1]+self.initial_freq_mode2)

                # Plot the fit
                fit_times = np.array(self.queue_time_mode2)
                fit_values = a2*fit_times + b2
                self.plot(fit_times - self.time_now, fit_values, 
                          pen=pg.mkPen(color=(100, 255, 100), width=2, style=Qt.DashLine), 
                          name='Mode 2 fit')
            else:
                self.req.set_dataset('__param__tracker/mode2/a', 0)
                self.req.set_dataset('__param__tracker/mode2/b', self.queue_freq_mode2[-1])
        elif len(self.queue_freq_mode2) > 0:
            # Not enough points for fitting, set a=b=0, c=current frequency
            self.req.set_dataset('__param__tracker/mode2/a', 0)
            self.req.set_dataset('__param__tracker/mode2/b', self.queue_freq_mode2[-1])
                
        
        # Single ion mode fitting
        if self.initial_freq_single_ion is not None and len(self.queue_freq_single_ion) > 0:
            # Get indices of points within last 2 hours
            recent_indices = [i for i, t in enumerate(self.queue_time_single_ion) if t > two_hours_ago]
            
            # Get recent points
            if len(recent_indices) > num_points_threshold:
                recent_times = np.array(self.queue_time_single_ion)[recent_indices]
                # Calculate drift for fitting
                recent_freqs = np.array(self.queue_freq_single_ion)[recent_indices] - self.initial_freq_single_ion
                recent_errors = np.array(self.queue_freq_single_ion_var)[recent_indices]

                recent_freqs=recent_freqs[-num_points:]
                recent_times=recent_times[-num_points:]
                recent_errors=recent_errors[-num_points:]
                
                # Calculate weights from errors (inverse variance weighting)
                # Avoid division by zero by adding small epsilon
                epsilon = 1e-10
                weights = 1.0 / (recent_errors + epsilon)
                
                try:
                    a3, b3 = self.fit_linear(recent_times, recent_freqs, weights=weights)
                    # Store coefficients in dataset
                    self.req.set_dataset('__param__tracker/mode_single_ion/a', a3)
                    self.req.set_dataset('__param__tracker/mode_single_ion/b', b3+self.initial_freq_single_ion)
                except Exception as e:
                    print(f"Error fitting mode single ion: {e}")
                    a3=0
                    b3=recent_freqs[-1]
                    self.req.set_dataset('__param__tracker/mode_single_ion/a', 0)
                    self.req.set_dataset('__param__tracker/mode_single_ion/b', recent_freqs[-1]+self.initial_freq_single_ion)

                # Plot the fit
                fit_times = np.array(self.queue_time_single_ion)
                fit_values = a3*fit_times + b3
                self.plot(fit_times - self.time_now, fit_values, 
                          pen=pg.mkPen(color=(100, 100, 255), width=2, style=Qt.DashLine), 
                          name='Single ion fit')
            else:
                self.req.set_dataset('__param__tracker/mode_single_ion/a', 0)
                self.req.set_dataset('__param__tracker/mode_single_ion/b', self.queue_freq_single_ion[-1])
        elif len(self.queue_freq_single_ion) > 0:
            # Not enough points for fitting, set a=b=0, c=current frequency
            self.req.set_dataset('__param__tracker/mode_single_ion/a', 0)
            self.req.set_dataset('__param__tracker/mode_single_ion/b', self.queue_freq_single_ion[-1])
                

        #################################
def main():
    applet = SimpleApplet(Drift_Tracker)
    applet.add_dataset("freq_mode1", "Mode 1 frequency")
    applet.add_dataset("freq_mode2", "Mode 2 frequency")
    applet.add_dataset("freq_mode_single_ion", "Single ion mode frequency")

    applet.add_dataset("freq_mode1_var", "Mode 1 frequency error")
    applet.add_dataset("freq_mode2_var", "Mode 2 frequency error")
    applet.add_dataset("freq_mode_single_ion_var", "Single ion mode frequency error")

    applet.run()


if __name__ == "__main__":
    main()
