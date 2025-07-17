"""
Fitting module for ARTIQ experiments providing various curve fitting functions.
"""

import numpy as np
from scipy.fft import fft, fftfreq
from scipy.optimize import curve_fit
from scipy.special import wofz
from scipy.signal import savgol_filter, find_peaks
from artiq.experiment import *

# Available fitting types
FITTING_TYPES = [
    'Lorentzian',
    'Lorentzian_2_peaks',
    'NLorentzian',
    'Gaussian',
    'Sin',
    'Voigt',
    'Exp_decay',
    'Voigt_Split',
    'Savgol_filter'
]

class Fitting:
    """Main class for handling curve fitting operations in ARTIQ experiments."""
    
    def __init__(self):
        """Initialize the Fitting class."""
        self.exp = None
        self.fitted_array = None

    def set_exp(self, exp):
        """Set the experiment instance."""
        self.exp = exp
    
    def initialize(self, exp, default_func: str, default_arg: float):
        """
        Initialize fitting parameters for the experiment.
        
        Args:
            exp: The experiment instance
            default_func: Default fitting function type
            default_arg: Default argument for fitting
        """
        self.set_exp(exp)

        if default_func not in FITTING_TYPES:
            raise RuntimeError("Unsupported Default Fitting Type")

        self.exp.setattr_argument(
            "Fit_Type", 
            EnumerationValue(FITTING_TYPES, default=default_func), 
            group='Fitting_Arguments'
        )

        self.exp.setattr_argument(
            "fit_arg", 
            NumberValue(default=default_arg, precision=6),
            tooltip="Argument for fitting",
            group='Fitting_Arguments'
        )
    
    def setup(self, array_length: int):
        """Setup the fitting dataset with specified array length."""
        self.exp.experiment_data.set_list_dataset('fit_signal', array_length, broadcast=True)
    
    def fit(self, x_data: np.ndarray, y_data: np.ndarray):
        """
        Perform fitting on the provided data.
        
        Args:
            x_data: X-axis data points
            y_data: Y-axis data points
            
        Returns:
            Fitting parameters if successful
        """
        is_success, fitted_array, params = fit_function(x_data, y_data, self.exp.Fit_Type, self.exp.fit_arg)
        self.fitted_array = fitted_array

        if is_success:
            self.exp.set_dataset('fit_signal', fitted_array, broadcast=True)

        return params

# Create a global instance
fitting_func = Fitting()

def fit_function(x_data: np.ndarray, y_data: np.ndarray, fit_type: str, guess: float = None):
    """
    Main fitting function that routes to specific fitting implementations.
    
    Args:
        x_data: X-axis data points
        y_data: Y-axis data points
        fit_type: Type of fitting to perform
        guess: Initial guess for fitting parameters
        
    Returns:
        Tuple of (success_flag, fitted_curve, parameters)
    """
    if np.abs(guess + 999) < 1e-3:
        guess = None
        
    fit_functions = {
        'Lorentzian': find_peak_lorentzian,
        'Lorentzian_2_peaks': find_peak_lorentzian_2_peaks,
        'NLorentzian': find_peak_Nlorentzian,
        'Sin': perform_fft_and_fit,
        'Voigt': fit_voigt,
        'Voigt_Split': fit_voigt_split,
        'Exp_decay': fit_exp_decay,
        'Savgol_filter': LPF_Savgol
    }
    
    if fit_type not in fit_functions:
        raise RuntimeError("Unsupported Fitting Type")
        
    return fit_functions[fit_type](x_data, y_data, guess)

def LPF_Savgol(x_data: np.ndarray, y_data: np.ndarray, guess: float = None) -> tuple[bool, np.ndarray, None]:
    """
    Apply Savitzky-Golay filter for low-pass filtering.
    
    Args:
        x_data: X-axis data points
        y_data: Y-axis data points
        guess: Not used in this function
        
    Returns:
        Tuple of (True, filtered_data, None)
    """
    fitted_curve = savgol_filter(y_data, window_length=7, polyorder=3)
    return True, fitted_curve, None

def find_peak_lorentzian_2_peaks(x_data: np.ndarray, y_data: np.ndarray, guess: float = None) -> tuple[bool, np.ndarray, np.ndarray]:
    """
    Fit two Lorentzian peaks with a common offset to the provided data using automatic peak detection.
    
    The model used is:
        L(x) = (amp1 * (width1**2 / ((x - center1)**2 + width1**2)) +
                amp2 * (width2**2 / ((x - center2)**2 + width2**2))) + offset
    
    Args:
        x_data: X-axis data points
        y_data: Y-axis data points
        guess: Not used in this function
        
    Returns:
        Tuple of (success_flag, fitted_curve, parameters)
    """
    x_data = np.array(x_data)
    y_data = np.array(y_data)
    
    # Detect peaks in the data
    peaks, properties = find_peaks(y_data, height=0)
    if len(peaks) < 2:
        print("Less than two peaks detected. Please check your data.")
        return False, y_data, None
    
    # If more than two peaks are detected, select the two with the highest amplitudes
    if len(peaks) > 2:
        peak_heights = properties["peak_heights"]
        highest_indices = np.argsort(peak_heights)[-2:]
        peaks = peaks[highest_indices]
    
    # Sort the detected peaks by their x position
    peaks = np.sort(peaks)
    
    # Estimate parameters
    offset_guess = np.min(y_data)
    amp1_guess = y_data[peaks[0]] - offset_guess
    center1_guess = x_data[peaks[0]]
    amp2_guess = y_data[peaks[1]] - offset_guess 
    center2_guess = x_data[peaks[1]]
    width_guess = (np.max(x_data) - np.min(x_data)) / 20
    
    initial_guess = [amp1_guess, center1_guess, width_guess,
                    amp2_guess, center2_guess, width_guess,
                    offset_guess]
    
    def double_lorentzian(x, amp1, center1, width1, amp2, center2, width2, offset):
        return (amp1 * (width1**2 / ((x - center1)**2 + width1**2)) +
                amp2 * (width2**2 / ((x - center2)**2 + width2**2)) +
                offset)
    
    try:
        params, _ = curve_fit(double_lorentzian, x_data, y_data, p0=initial_guess)
    except RuntimeError:
        print("Fitting Failed!!")
        return False, y_data, None
    
    fitted_curve = double_lorentzian(x_data, *params)
    
    print('Fitted Widths:  ', params[2], params[5])
    print('Fitted Centers: ', params[1], params[4])
    
    return True, fitted_curve, params

def find_peak_lorentzian(x_data: np.ndarray, y_data: np.ndarray, 
                        guess_peak: float = None, guess_amplitude: float = None,
                        guess_width: float = None, guess_offset: float = None) -> tuple[bool, np.ndarray, np.ndarray]:
    """
    Fit a single Lorentzian peak to the data.
    
    Args:
        x_data: X-axis data points
        y_data: Y-axis data points
        guess_peak: Initial guess for peak position
        guess_amplitude: Initial guess for peak amplitude
        guess_width: Initial guess for peak width
        guess_offset: Initial guess for baseline offset
        
    Returns:
        Tuple of (success_flag, fitted_curve, parameters)
    """
    if guess_peak is None:
        guess_peak = x_data[np.argmax(y_data)]
    if guess_amplitude is None:
        guess_amplitude = max(y_data) - min(y_data)
    if guess_width is None:
        half_max = guess_amplitude / 2 + min(y_data)
        indices_above_half_max = np.where(y_data >= half_max)[0]
        
        if len(indices_above_half_max) > 1:
            fwhm_guess = x_data[indices_above_half_max[-1]] - x_data[indices_above_half_max[0]]
        else:
            fwhm_guess = np.max(x_data)/4 - np.min(x_data)/4
            
        guess_width = fwhm_guess
        print("Guess width: ", guess_width)
        
    if guess_offset is None:
        guess_offset = min(y_data)

    initial_guess = [guess_amplitude, guess_peak, guess_width, guess_offset]

    def lorentzian(x, amplitude, center, width, offset):
        return amplitude * (width**2 / ((x - center)**2 + width**2)) + offset

    try:
        params, _ = curve_fit(lorentzian, x_data, y_data, p0=initial_guess)
    except RuntimeError:
        print("Fitting Failed!!")
        return False, y_data, params

    fitted_amplitude, fitted_center, fitted_width, fitted_offset = params
    fitted_curve = lorentzian(x_data, fitted_amplitude, fitted_center, fitted_width, fitted_offset)

    print('Fitted Width:     ', fitted_width)
    print('Fitted Frequency: ', fitted_center, ' MHz')

    return True, fitted_curve, params



def find_peak_lorentzian_with_error(x_data: np.ndarray, y_data: np.ndarray, 
                        guess_peak: float = None, guess_amplitude: float = None,
                        guess_width: float = None, guess_offset: float = None) -> tuple[bool, np.ndarray, float, float]:
    """
    Fit a single Lorentzian peak to the data and return peak position with error.
    
    Args:
        x_data: X-axis data points
        y_data: Y-axis data points
        guess_peak: Initial guess for peak position
        guess_amplitude: Initial guess for peak amplitude
        guess_width: Initial guess for peak width
        guess_offset: Initial guess for baseline offset
        
    Returns:
        Tuple of (success_flag, fitted_curve, peak_position, peak_position_error)
    """
    if guess_peak is None:
        guess_peak = x_data[np.argmax(y_data)]
    if guess_amplitude is None:
        guess_amplitude = max(y_data) - min(y_data)
    if guess_width is None:
        half_max = guess_amplitude / 2 + min(y_data)
        indices_above_half_max = np.where(y_data >= half_max)[0]
        
        if len(indices_above_half_max) > 1:
            fwhm_guess = x_data[indices_above_half_max[-1]] - x_data[indices_above_half_max[0]]
        else:
            fwhm_guess = np.max(x_data)/4 - np.min(x_data)/4
            
        guess_width = fwhm_guess
        print("Guess width: ", guess_width)
        
    if guess_offset is None:
        guess_offset = min(y_data)

    initial_guess = [guess_amplitude, guess_peak, guess_width, guess_offset]

    def lorentzian(x, amplitude, center, width, offset):
        return amplitude * (width**2 / ((x - center)**2 + width**2)) + offset

    try:
        params, covariance = curve_fit(lorentzian, x_data, y_data, p0=initial_guess)
        # Calculate parameter errors from covariance matrix
        param_errors = np.sqrt(np.diag(covariance))
        peak_position = params[1]  # Center parameter
        peak_position_error = param_errors[1]  # Error in the center parameter
        fitted_curve = lorentzian(x_data, *params)
    except RuntimeError:
        print("Fitting Failed!!")
        return False, y_data, 0.0, 0.0

    print('Fitted Width:     ', params[2])
    print('Fitted Frequency: ', peak_position, ' MHz')
    print('Peak Position Error: ', peak_position_error, ' MHz')

    return True, fitted_curve, peak_position, peak_position_error


def find_peak_gaussian_with_error(x_data: np.ndarray, y_data: np.ndarray, 
                        guess_peak: float = None, guess_amplitude: float = None,
                        guess_width: float = None, guess_offset: float = None) -> tuple[bool, np.ndarray, float, float]:
    """
    Fit a single Gaussian peak to the data and return peak position with error.
    
    Args:
        x_data: X-axis data points
        y_data: Y-axis data points
        guess_peak: Initial guess for peak position
        guess_amplitude: Initial guess for peak amplitude
        guess_width: Initial guess for peak width (sigma)
        guess_offset: Initial guess for baseline offset
        
    Returns:
        Tuple of (success_flag, fitted_curve, peak_position, peak_position_error)
    """
    # Advanced parameter guessing for robustness
    if guess_peak is None:
        # Find peak by smoothing data first to reduce noise
        from scipy.ndimage import gaussian_filter1d
        smoothed_y = gaussian_filter1d(y_data, sigma=1.0)
        guess_peak = x_data[np.argmax(smoothed_y)]
    
    if guess_amplitude is None:
        # Use robust amplitude estimation
        y_sorted = np.sort(y_data)
        baseline_est = np.mean(y_sorted[:len(y_sorted)//4])  # Bottom 25%
        peak_est = np.mean(y_sorted[-len(y_sorted)//10:])    # Top 10%
        guess_amplitude = peak_est - baseline_est
    
    if guess_width is None:
        # Estimate width from FWHM with improved robustness
        if guess_offset is None:
            baseline = np.mean(np.concatenate([y_data[:len(y_data)//10], y_data[-len(y_data)//10:]]))
        else:
            baseline = guess_offset
            
        half_max = guess_amplitude / 2 + baseline
        indices_above_half_max = np.where(y_data >= half_max)[0]
        
        if len(indices_above_half_max) > 1:
            fwhm_guess = x_data[indices_above_half_max[-1]] - x_data[indices_above_half_max[0]]
            # Convert FWHM to sigma for Gaussian: sigma = FWHM / (2 * sqrt(2 * ln(2)))
            guess_width = fwhm_guess / (2 * np.sqrt(2 * np.log(2)))
        else:
            # Fallback: use data range
            guess_width = (np.max(x_data) - np.min(x_data)) / 8
            
        print("Guess width (sigma): ", guess_width)
        
    if guess_offset is None:
        # Robust baseline estimation
        y_sorted = np.sort(y_data)
        guess_offset = np.mean(y_sorted[:len(y_sorted)//4])  # Bottom 25%

    initial_guess = [guess_amplitude, guess_peak, guess_width, guess_offset]

    def gaussian(x, amplitude, center, sigma, offset):
        return amplitude * np.exp(-0.5 * ((x - center) / sigma)**2) + offset

    try:
        # Set reasonable bounds to improve fitting robustness
        x_range = np.max(x_data) - np.min(x_data)
        y_range = np.max(y_data) - np.min(y_data)
        
        bounds = (
            [0, np.min(x_data), 0, np.min(y_data) - y_range],  # Lower bounds
            [y_range * 2, np.max(x_data), x_range, np.max(y_data) + y_range]  # Upper bounds
        )
        
        params, covariance = curve_fit(gaussian, x_data, y_data, p0=initial_guess, bounds=bounds)
        # Calculate parameter errors from covariance matrix
        param_errors = np.sqrt(np.diag(covariance))
        peak_position = params[1]  # Center parameter
        peak_position_error = param_errors[1]  # Error in the center parameter
        fitted_curve = gaussian(x_data, *params)
    except (RuntimeError, ValueError) as e:
        print(f"Gaussian fitting failed: {e}")
        return False, y_data, 0.0, 0.0

    print('Fitted Width (sigma): ', params[2])
    print('Fitted Frequency: ', peak_position, ' MHz')
    print('Peak Position Error: ', peak_position_error, ' MHz')

    return True, fitted_curve, peak_position, peak_position_error


def find_peak_Nlorentzian(x_data: np.ndarray, y_data: np.ndarray,
                         guess_peak: float = None, guess_amplitude: float = None,
                         guess_width: float = None, guess_offset: float = None) -> tuple[bool, np.ndarray, np.ndarray]:
    """
    Fit a negative Lorentzian peak to the data.
    
    Args:
        x_data: X-axis data points
        y_data: Y-axis data points
        guess_peak: Initial guess for peak position
        guess_amplitude: Initial guess for peak amplitude
        guess_width: Initial guess for peak width
        guess_offset: Initial guess for baseline offset
        
    Returns:
        Tuple of (success_flag, fitted_curve, parameters)
    """
    y_data_here = -y_data
    
    if guess_peak is None:
        guess_peak = x_data[np.argmax(y_data_here)]
    if guess_amplitude is None:
        guess_amplitude = max(y_data_here) - min(y_data_here)
    if guess_width is None:
        half_max = guess_amplitude / 2 + min(y_data_here)
        indices_above_half_max = np.where(y_data_here >= half_max)[0]
        
        if len(indices_above_half_max) > 1:
            fwhm_guess = x_data[indices_above_half_max[-1]] - x_data[indices_above_half_max[0]]
        else:
            fwhm_guess = np.max(x_data)/4 - np.min(x_data)/4
            
        guess_width = fwhm_guess
        print("Guess width: ", guess_width)
        
    if guess_offset is None:
        guess_offset = min(y_data_here)

    initial_guess = [guess_amplitude, guess_peak, guess_width, guess_offset]

    def lorentzian(x, amplitude, center, width, offset):
        return amplitude * (width**2 / ((x - center)**2 + width**2)) + offset

    try:
        params, _ = curve_fit(lorentzian, x_data, y_data_here, p0=initial_guess)
    except RuntimeError:
        print("Fitting Failed!!")
        return False, y_data, params

    fitted_amplitude, fitted_center, fitted_width, fitted_offset = params
    fitted_amplitude *= -1
    fitted_offset *= -1

    fitted_curve = lorentzian(x_data, fitted_amplitude, fitted_center, fitted_width, fitted_offset)

    print('Fitted Width:     ', fitted_width)
    print('Fitted Frequency: ', fitted_center, ' MHz')

    return True, fitted_curve, params

def find_peak_gaussian(x_data: np.ndarray, y_data: np.ndarray, guess_peak: float = None) -> tuple[bool, np.ndarray, np.ndarray]:
    """
    Fit a Gaussian peak to the data.
    
    Args:
        x_data: X-axis data points
        y_data: Y-axis data points
        guess_peak: Initial guess for peak position
        
    Returns:
        Tuple of (success_flag, fitted_curve, parameters)
    """
    if guess_peak is None:
        guess_peak = x_data[np.argmax(y_data)]

    guess_offset = min(y_data)
    guess_amplitude = max(y_data) - min(y_data)

    half_max = guess_amplitude / 2 + guess_offset
    indices_above_half_max = np.where(y_data >= half_max)[0]
    if len(indices_above_half_max) > 1:
        fwhm_guess = x_data[indices_above_half_max[-1]] - x_data[indices_above_half_max[0]]
    else:
        fwhm_guess = np.max(x_data)/4 - np.min(x_data)/4

    guess_width = fwhm_guess / 2.355
    initial_guess = [guess_amplitude, guess_peak, guess_width, guess_offset]

    def gaussian(x, a, x0, sigma, offset):
        return a * np.exp(-(x - x0) ** 2 / (2 * sigma ** 2)) + offset

    try:
        params, _ = curve_fit(gaussian, x_data, y_data, p0=initial_guess)
    except RuntimeError:
        print("Fitting Failed!!")
        return False, y_data, None

    fitted_amplitude, fitted_center, fitted_width, fitted_offset = params
    fitted_curve = gaussian(x_data, fitted_amplitude, fitted_center, fitted_width, fitted_offset)

    print('Fitted Width:     ', fitted_width)
    print('Fitted Frequency: ', fitted_center, ' MHz')

    return True, fitted_curve, params

def low_pass_filter_time_domain(data: np.ndarray, dt: float) -> np.ndarray:
    """
    Low-pass filter a 1D signal by removing frequency components above 1/(4*dt).
    
    Args:
        data: The time-domain signal to filter (1D)
        dt: The sampling interval (time between samples)
        
    Returns:
        The filtered signal in the time domain
    """
    N = len(data)
    freqs = np.fft.fftfreq(N, d=dt)
    Y = np.fft.fft(data)

    cutoff_freq = 1.0 / (3.5 * dt)
    Y_filtered = np.where(np.abs(freqs) > cutoff_freq, 0.0, Y)
    filtered_data = np.fft.ifft(Y_filtered)
    
    return filtered_data.real

def perform_fft_and_fit(time: np.ndarray, signal: np.ndarray, guess: float = None) -> tuple[bool, np.ndarray, np.ndarray]:
    """
    Perform FFT analysis and fit a damped sine wave to the data.
    
    Args:
        time: Time points
        signal: Signal values
        guess: Initial phase guess
        
    Returns:
        Tuple of (success_flag, fitted_curve, parameters)
    """
    smoothed_signal = low_pass_filter_time_domain(signal, time[1]-time[0])
    
    if guess is None:
        guess = np.pi / 2 if smoothed_signal[0] > np.mean(smoothed_signal) else 0

    N = time.size
    T = time[1] - time[0]
    yf = fft(smoothed_signal)
    xf = fftfreq(N, T)[:N // 2]
    yf[0] = 0

    power_spectrum = 2.0 / N * np.abs(yf[:N // 2])
    threshold = np.max(power_spectrum) * 0.1
    dominant_frequency_idx = np.where(power_spectrum > threshold)[0]
    dominant_frequency = xf[dominant_frequency_idx[np.argmax(power_spectrum[dominant_frequency_idx])]]

    print("Estimated Dominant Frequency: ", dominant_frequency, 'MHz')

    def sine_function(t, A, omega, phi, tau, c):
        return A * np.sin(omega * t + phi) * np.exp(-t / tau) + c

    initial_guess = [
        np.ptp(smoothed_signal) / 2,
        2 * np.pi * dominant_frequency,
        guess,
        (time[-1] - time[0]) / 2,
        np.mean(smoothed_signal)
    ]

    try:
        params, _ = curve_fit(sine_function, time, signal, p0=initial_guess)
        fitted_amplitude, fitted_omega, fitted_phase, fitted_tau, fitted_offset = params
        fitted_frequency = fitted_omega / (2 * np.pi)
        fitted_signal = sine_function(time, fitted_amplitude, fitted_omega, fitted_phase, fitted_tau, fitted_offset)

        print('Fitted Amplitude: ', fitted_amplitude)
        print('Fitted Frequency: ', fitted_frequency, ' MHz')
        print('Fitted Phase:     ', fitted_phase)
        print('PI time:          ', 1 / fitted_frequency / 2, ' us')
        print('Tau:              ', fitted_tau, ' us')

        return True, fitted_signal, params
    except RuntimeError:
        print("Fitting Failed!!")
        return False, None, None

def fit_voigt(time: np.ndarray, signal: np.ndarray, guess_peak: float = None) -> tuple[bool, np.ndarray, np.ndarray]:
    """
    Fit a Voigt profile to the data.
    
    Args:
        time: Time points
        signal: Signal values
        guess_peak: Initial guess for peak position
        
    Returns:
        Tuple of (success_flag, fitted_curve, parameters)
    """
    print("Fitting Voigt!")

    if guess_peak is None:
        guess_peak = time[np.argmax(signal)]

    def voigt(x, amplitude, center, sigma, gamma):
        z = ((x - center) + 1j*gamma) / (sigma * np.sqrt(2))
        return amplitude * np.real(wofz(z)) / (sigma * np.sqrt(2*np.pi))

    initial_guess = [np.max(signal), time[np.argmax(signal)], 1, 1]

    try:
        params, _ = curve_fit(voigt, time, signal, p0=initial_guess)
    except RuntimeError:
        print("Fitting Failed!!")
        return False, signal, None

    fitted_amplitude, fitted_center, fitted_width, fitted_offset = params
    fitted_curve = voigt(time, fitted_amplitude, fitted_center, fitted_width, fitted_offset)

    print('Fitted Width:     ', fitted_width)
    print('Fitted Frequency: ', fitted_center, ' MHz')

    return True, fitted_curve, params

def fit_voigt_split(time: np.ndarray, signal: np.ndarray, guess_peak: float = None) -> tuple[bool, np.ndarray, np.ndarray]:
    """
    Fit a split Voigt profile to the data.
    
    Args:
        time: Time points
        signal: Signal values
        guess_peak: Initial guess for peak position
        
    Returns:
        Tuple of (success_flag, fitted_curve, parameters)
    """
    print("Fitting Splitted Voigt!")

    if guess_peak is None:
        guess_peak = time[np.argmax(signal)]
    
    def smooth_transition(x, center, sigma1, sigma2, width=1):
        return sigma1 + (sigma2 - sigma1) / (1 + np.exp(-(x - center) / width))

    def voigt(x, amplitude, center, sigma1, sigma2, gamma, transition_width):
        sigma = smooth_transition(x, center, sigma1, sigma2, transition_width)
        z = ((x - center) + 1j * gamma) / (sigma * np.sqrt(2))
        return amplitude * np.real(wofz(z)) / (sigma * np.sqrt(2 * np.pi))

    initial_guess = [np.max(signal), time[np.argmax(signal)], 1, 1, 1, 0.1]

    try:
        params, _ = curve_fit(voigt, time, signal, p0=initial_guess)
    except RuntimeError:
        print("Fitting Failed!!")
        return False, signal, None

    fitted_amplitude, fitted_center, fitted_width1, fitted_width2, fitted_gamma, fitted_tr = params
    fitted_curve = voigt(time, fitted_amplitude, fitted_center, fitted_width1, fitted_width2, fitted_gamma, fitted_tr)

    print('Fitted Width:     ', fitted_width1, ' ', fitted_width2)
    print('Fitted Frequency: ', fitted_center, ' MHz')

    return True, fitted_curve, params

def fit_exp_decay(time: np.ndarray, signal: np.ndarray, guess_tau: float = None) -> tuple[bool, np.ndarray, np.ndarray]:
    """
    Fit an exponential decay to the data.
    
    Args:
        time: Time points
        signal: Signal values
        guess_tau: Initial guess for decay time constant
        
    Returns:
        Tuple of (success_flag, fitted_curve, parameters)
    """
    print("Fitting Exponential Decay!")

    if guess_tau is None:
        offset_guess = np.min(signal)
        amplitude_guess = np.max(signal) - offset_guess
        target_value = offset_guess + amplitude_guess / np.e
        idx = np.argmin(np.abs(signal - target_value))
        guess_tau = time[idx] if time[idx] > 0 else 20
        print("Estimated guess_tau:", guess_tau)

    def exp_decay(x, amplitude, tau, offset):
        return amplitude * np.exp(-x / tau) + offset

    initial_guess = [np.max(signal) - np.min(signal), guess_tau, np.min(signal)]

    try:
        params, _ = curve_fit(exp_decay, time, signal, p0=initial_guess)
    except RuntimeError:
        print("Fitting Failed!!!!!!!!!")
        return False, signal, None

    fitted_amplitude, fitted_tau, fitted_offset = params
    fitted_curve = exp_decay(time, fitted_amplitude, fitted_tau, fitted_offset)

    print('Fitted Tau:     ', fitted_tau)
    print('Fitted Offset:  ', fitted_offset)

    return True, fitted_curve, params
