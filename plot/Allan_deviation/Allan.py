import numpy as np
import matplotlib.pyplot as plt
import json
from scipy import signal
import argparse

def calculate_allan_deviation(times, freqs, tau_max=None):
    """
    Calculate Allan deviation for a time series of frequencies.
    
    Args:
        times: Array of timestamps
        freqs: Array of frequencies
        tau_max: Maximum tau to calculate (in seconds). If None, uses half the total time.
    
    Returns:
        taus: Array of tau values
        allan_dev: Array of Allan deviations
    """
    # Calculate time differences
    dt = np.diff(times)
    if not np.allclose(dt, dt[0]):
        print("Warning: Non-uniform time steps detected")
    
    # Calculate fractional frequency
    y = np.diff(freqs) / freqs[:-1]
    
    # Calculate Allan deviation
    if tau_max is None:
        tau_max = (times[-1] - times[0]) / 2
    
    taus = np.logspace(np.log10(dt[0]), np.log10(tau_max), 100)
    allan_dev = np.zeros_like(taus)
    
    for i, tau in enumerate(taus):
        m = int(tau / dt[0])
        if m < 2:
            continue
            
        # Calculate Allan variance
        var = 0
        for j in range(len(y) - 2*m + 1):
            var += (np.sum(y[j:j+m]) - np.sum(y[j+m:j+2*m]))**2
        var /= (2 * (len(y) - 2*m + 1) * m**2)
        
        allan_dev[i] = np.sqrt(var)
    
    return taus, allan_dev

def plot_allan_deviation(data_file, modes=None):
    """
    Load data and plot Allan deviation for each mode.
    
    Args:
        data_file: Path to the JSON data file
        modes: List of modes to analyze. If None, analyzes all available modes.
    """
    # Load data
    with open(data_file, 'r') as f:
        data = json.load(f)
    
    plt.figure(figsize=(10, 6))
    
    # If no modes specified, use all available modes
    if modes is None:
        modes = ['mode1', 'mode2', 'single_ion']
    
    # Process each specified mode
    for mode in modes:
        if mode in data:
            times = np.array(data[mode]['times'])
            freqs = np.array(data[mode]['freqs'])

            plt.plot(times, freqs)
            plt.show()
            
            # Calculate Allan deviation
            taus, allan_dev = calculate_allan_deviation(times, freqs)
            
            # Plot
            plt.loglog(taus, allan_dev, label=mode)
        else:
            print(f"Warning: Mode '{mode}' not found in data file")
    
    plt.xlabel('Averaging Time (s)')
    plt.ylabel('Allan Deviation')
    plt.title('Allan Deviation vs Averaging Time')
    plt.grid(True)
    plt.legend()
    plt.show()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Calculate and plot Allan deviation for frequency data.')
    parser.add_argument('--data-file', type=str, default="./drift_tracker_motion_20250524_001752.json",
                      help='Path to the JSON data file')
    parser.add_argument('--modes', type=str, nargs='+', choices=['mode1', 'mode2', 'single_ion'],
                      help='Modes to analyze (e.g., --modes mode1 mode2)')
    
    args = parser.parse_args()
    plot_allan_deviation(args.data_file, args.modes)
