
import numpy as np
from scipy.fft import fft, fftfreq
from scipy.optimize import curve_fit
from scipy.special import wofz
from scipy.signal import savgol_filter
from artiq.experiment import *

fitting_types=['Lorentzian', 'Gaussian', 'Sin', 'Voigt', 'Exp_decay', 'Voigt_Split', 'Savgol_filter']

class fitting:
    def __init__(self):
        self.exp=None

    def setExp(self, exp):
        self.exp=exp
    
    def initialize(self, exp, default_func, default_arg):
        self.setExp(exp)

        if not default_func in fitting_types:
            raise RuntimeError("Unsupported Default Fitting Type")

        self.exp.setattr_argument("Fit_Type", EnumerationValue(fitting_types, default=default_func), group='Fitting_Arguments')

        self.exp.setattr_argument(
            "fit_arg", NumberValue(default=default_arg, precision=6),
            tooltip="Argument for fitting",
            group='Fitting_Arguments'
        )

       
    
    def setup(self, array_length):
        self.exp.experiment_data.set_list_dataset('fit_signal', array_length, broadcast=True)
    
    def fit(self, x_data, y_data):

        is_success, fitted_array, params=fit_function(x_data, y_data, self.exp.Fit_Type, self.exp.fit_arg)

        self.fitted_array=fitted_array

        if is_success:
            self.exp.set_dataset('fit_signal', fitted_array, broadcast=True)

        return params

fitting_func=fitting()

def fit_function(x_data, y_data, fit_type, guess=None):

    if np.abs(guess+999)<1e-3: guess=None
    if fit_type=='Lorentzian':
        return find_peak_lorentzian(x_data, y_data, guess)
    elif fit_type=='Sin':
        return perform_fft_and_fit(x_data, y_data, guess)
    elif fit_type=='Voigt':
        return fit_voigt(x_data,y_data,guess)
    elif fit_type=='Voigt_Split':
        return fit_voigt_split(x_data,y_data,guess)
    elif fit_type=='Exp_decay':
        return fit_exp_decay(x_data,y_data,guess)
    elif fit_type=='Savgol_filter':
        return LPF_Savgol(x_data,y_data,guess)
    else:
        raise RuntimeError("Unsupported Fitting Type")

def LPF_Savgol(x_data, y_data, guess):

    fitted_curve=savgol_filter(y_data, window_length=7, polyorder=3)


    return True, fitted_curve, None

# Function to perform Lorentzian fitting and find the peak
def find_peak_lorentzian(x_data, y_data, guess_peak=None, guess_amplitude=None, guess_width=None, guess_offset=None):
    if guess_peak==None:
        guess_peak=x_data[np.argmax(y_data)]
    if guess_amplitude==None:
        guess_amplitude=max(y_data)-min(y_data)
    if guess_width==None:
        # Estimate of half maximum
        half_max = guess_amplitude / 2 +min(y_data)

        # Find points where the data crosses the half-maximum
        indices_above_half_max = np.where(y_data >= half_max)[0]

        # FWHM is the difference between the first and last index crossing the half-max
        if len(indices_above_half_max) > 1:
            fwhm_guess = x_data[indices_above_half_max[-1]] - x_data[indices_above_half_max[0]]
        else:
            fwhm_guess = np.max(x_data)/4-np.min(x_data)/4 # Fallback in case the peak is not well defined

        # Set initial guess for gamma (FWHM is related to gamma by FWHM = gamma)
        guess_width = fwhm_guess

        print("Guess width: ",guess_width)
    if guess_offset==None:
        guess_offset=min(y_data)

    # Initial guess for the parameters: amplitude, center, and width
    initial_guess = [guess_amplitude, guess_peak, guess_width, guess_offset]

    def lorentzian(x, amplitude, center, width, offset):
        return amplitude * (width**2 / ((x - center)**2 + width**2)) +offset

    try:
        # Perform the curve fitting
        params, params_covariance = curve_fit(lorentzian, x_data, y_data, p0=initial_guess)
    except RuntimeError:
        print("Fitting Failed!!")
        return False, y_data, params

    # Extract the fitted parameters
    fitted_amplitude, fitted_center, fitted_width, fitted_offset = params

    # Generate the fitted Lorentzian curve
    fitted_curve = lorentzian(x_data, fitted_amplitude, fitted_center, fitted_width, fitted_offset)

    print('Fitted Width:     ', fitted_width)
    print('Fitted Frequency: ', fitted_center, ' MHz')

    return True, fitted_curve, params

# Function to perform Gaussian fitting and find the peak
def find_peak_gaussian(x_data, y_data, guess_peak=None):
    if guess_peak==None:
        guess_peak=x_data[np.argmax(y_data)]

    guess_offset = min(y_data)
    guess_amplitude=max(y_data)-min(y_data)

    # Estimate of half maximum
    half_max = guess_amplitude / 2 +guess_offset
    indices_above_half_max = np.where(y_data >= half_max)[0]
    if len(indices_above_half_max) > 1:
        fwhm_guess = x_data[indices_above_half_max[-1]] - x_data[indices_above_half_max[0]]
    else:
        fwhm_guess = np.max(x_data)/4-np.min(x_data)/4  # Fallback in case the peak is not well defined

    # Calculate sigma from FWHM
    guess_width = fwhm_guess / 2.355

    # Initial guess for the parameters: amplitude, center, and width
    initial_guess = [guess_amplitude, guess_peak, guess_width , guess_offset ]

    def gaussian(x, a, x0, sigma, offset):
        return a * np.exp(-(x - x0) ** 2 / (2 * sigma ** 2)) +offset

    try:
        # Perform the curve fitting
        params, params_covariance = curve_fit(gaussian, x_data, y_data, p0=initial_guess)
    except RuntimeError:
        print("Fitting Failed!!")
        return False, y_data

    # Extract the fitted parameters
    fitted_amplitude, fitted_center, fitted_width, fitted_offset = params

    # Generate the fitted Lorentzian curve
    fitted_curve = gaussian(x_data, fitted_amplitude, fitted_center, fitted_width, fitted_offset)

    print('Fitted Width:     ', fitted_width)
    print('Fitted Frequency: ', fitted_center, ' MHz')

    return True, fitted_curve, params

def low_pass_filter_time_domain(data, dt):
    """
    Low-pass filter a 1D signal by removing frequency components above 1/(4*dt).
    
    Parameters:
    -----------
    data : array_like
        The time-domain signal to filter (1D).
    dt   : float
        The sampling interval (time between samples).
        
    Returns:
    --------
    filtered_data : numpy.ndarray
        The filtered signal in the time domain.
    """
    
    N = len(data)                       # number of samples
    freqs = np.fft.fftfreq(N, d=dt)     # frequency bins for the FFT
    Y = np.fft.fft(data)                # compute the FFT of the signal

    # Define the cutoff frequency
    cutoff_freq = 1.0 / (3.5 * dt)

    # Zero out all frequency components whose magnitude is above the cutoff
    Y_filtered = np.where(np.abs(freqs) > cutoff_freq, 0.0, Y)

    # Transform back to time domain
    filtered_data = np.fft.ifft(Y_filtered)
    
    # If the original data is real, you can take the real part
    filtered_data = filtered_data.real

    return filtered_data

def perform_fft_and_fit(time, signal, guess=None):
    # Smooth the signal using Savitzky-Golay filter to remove high-frequency noise
    smoothed_signal = low_pass_filter_time_domain(signal, time[1]-time[0])
    #savgol_filter(signal, window_length=11, polyorder=3)
    
    if guess is None:
        guess = np.pi / 2 if smoothed_signal[0] > np.mean(smoothed_signal) else 0

    # Perform FFT on the smoothed signal
    N = time.size
    T = time[1] - time[0]
    yf = fft(smoothed_signal)
    xf = fftfreq(N, T)[:N // 2]
    yf[0] = 0

    # Coarsely determine the dominant frequency by ignoring very high frequencies
    power_spectrum = 2.0 / N * np.abs(yf[:N // 2])
    threshold = np.max(power_spectrum) * 0.1  # Ignore peaks below 10% of the max
    dominant_frequency_idx = np.where(power_spectrum > threshold)[0]
    dominant_frequency = xf[dominant_frequency_idx[np.argmax(power_spectrum[dominant_frequency_idx])]]

    print("Estimated Dominant Frequency: ", dominant_frequency, 'MHz')

    # Define the sine function for fitting
    def sine_function(t, A, omega, phi, tau, c):
        return A * np.sin(omega * t + phi) * np.exp(-t / tau) + c

    # Initial guess for the parameters
    initial_guess = [
        np.ptp(smoothed_signal) / 2,  # Amplitude guess
        2 * np.pi * dominant_frequency,  # Omega guess
        guess,  # Phase guess
        (time[-1] - time[0]) / 2,  # Tau guess
        np.mean(smoothed_signal)  # Offset guess
    ]
    
    # Parameter bounds to ensure reasonable fitting
    # bounds = (
    #     [0, 0, -2 * np.pi, 0, -np.inf],  # Lower bounds
    #     [np.inf, np.inf, 2 * np.pi, np.inf, np.inf]  # Upper bounds
    # )

    # Perform the curve fitting
    try:
        params, params_covariance = curve_fit(
            sine_function, time, signal, p0=initial_guess#, bounds=bounds
        )

        # Extract the fitted parameters
        fitted_amplitude, fitted_omega, fitted_phase, fitted_tau, fitted_offset = params
        fitted_frequency = fitted_omega / (2 * np.pi)

        # Generate the fitted sine wave
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
    
    
def fit_voigt(time, signal, guess_peak=None):

    print("Fitting Voigt!")

    if guess_peak==None:
        guess_peak=time[np.argmax(signal)]

    # Define the Voigt function
    def voigt(x, amplitude, center, sigma, gamma):
        z = ((x - center) + 1j*gamma) / (sigma * np.sqrt(2))
        return amplitude * np.real(wofz(z)) / (sigma * np.sqrt(2*np.pi))


    # Initial guess for the parameters: amplitude, center, sigma, gamma
    initial_guess = [np.max(signal), time[np.argmax(signal)], 1, 1]

    try:
        # Perform the curve fitting
        params, params_covariance = curve_fit(voigt, time, signal, p0=initial_guess)
    except RuntimeError:
        print("Fitting Failed!!")
        return False, signal

    # Extract the fitted parameters
    fitted_amplitude, fitted_center, fitted_width, fitted_offset = params

    # Generate the fitted Lorentzian curve
    fitted_curve = voigt(time,  fitted_amplitude, fitted_center, fitted_width, fitted_offset)

    print('Fitted Width:     ', fitted_width)
    print('Fitted Frequency: ', fitted_center, ' MHz')

    return True, fitted_curve, params

def fit_voigt_split(time, signal, guess_peak=None):

    print("Fitting Splitted Voigt!")

    if guess_peak==None:
        guess_peak=time[np.argmax(signal)]


    
    def smooth_transition(x, center, sigma1, sigma2, width=1):
        """
        Create a smooth transition between sigma1 and sigma2 around the center.
        """
        return sigma1 + (sigma2 - sigma1) / (1 + np.exp(-(x - center) / width))

    def voigt(x, amplitude, center, sigma1, sigma2, gamma, transition_width):
        sigma = smooth_transition(x, center, sigma1, sigma2, transition_width)

        #sigma=np.where(x<center, sigma1, sigma2)
        z = ((x - center) + 1j * gamma) / (sigma * np.sqrt(2))

        # scale1=np.real(wofz(1j * gamma) / (sigma1 * np.sqrt(2))) / (sigma1)
        # scale2=np.real(wofz(1j * gamma) / (sigma2 * np.sqrt(2))) / (sigma2)

        # scale=np.where(x<center, 1,  scale1/scale2 )


        return amplitude * np.real(wofz(z)) / (sigma * np.sqrt(2 * np.pi))#*scale


    # # Define the Voigt function
    # def voigt(x, amplitude, center, sigma1, sigma2, gamma):
    #     sigma=np.where(x<center, sigma1, sigma2)
    #     z = ((x - center) + 1j*gamma) / (sigma * np.sqrt(2))
    #     return amplitude * np.real(wofz(z)) / (sigma * np.sqrt(2*np.pi))


    # Initial guess for the parameters: amplitude, center, sigma, gamma
    initial_guess = [np.max(signal), time[np.argmax(signal)], 1, 1, 1, 0.1]

    try:
        # Perform the curve fitting
        params, params_covariance = curve_fit(voigt, time, signal, p0=initial_guess)
    except RuntimeError:
        print("Fitting Failed!!")
        return False, signal

    # Extract the fitted parameters
    fitted_amplitude, fitted_center, fitted_width1, fitted_width2, fitted_gamma, fitted_tr= params

    # Generate the fitted Lorentzian curve
    fitted_curve = voigt(time,  fitted_amplitude, fitted_center, fitted_width1, fitted_width2, fitted_gamma, fitted_tr)

    print('Fitted Width:     ', fitted_width1, ' ', fitted_width2)
    print('Fitted Frequency: ', fitted_center, ' MHz')

    return True, fitted_curve, params
    
def fit_exp_decay(time, signal, guess_tau=None):

    print("Fitting Exponential Decay!")

    if guess_tau==None:
        guess_tau=20


    def expdecay(x, amplitude, tau, offset):
        return amplitude*np.exp(-x/tau)+offset


    # Initial guess for the parameters: amplitude, center, sigma, gamma
    initial_guess = [np.max(signal)-np.min(signal), guess_tau, np.min(signal)]

    try:
        # Perform the curve fitting
        params, params_covariance = curve_fit(expdecay, time, signal, p0=initial_guess)
    except RuntimeError:
        print("Fitting Failed!!!!!!!!!")
        return False, signal

    # Extract the fitted parameters
    fitted_amplitude, fitted_tau, fitted_offset = params

    # Generate the fitted Lorentzian curve
    fitted_curve = expdecay(time,  fitted_amplitude, fitted_tau, fitted_offset)

    print('Fitted Tau:     ', fitted_tau)
    print('Fitted Offset:  ', fitted_offset)

    return True, fitted_curve, params
