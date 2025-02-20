from acf.experiment import _ACFExperiment
from acf_sequences.sequences import sequences
from acf_config.arguments_definition import argument_manager

from artiq.experiment import *

from scipy.signal import find_peaks
from acf.function.fitting import *

# Function to model a Gaussian
def gaussian(x, a, x0, sigma):
    return a * np.exp(-(x - x0) ** 2 / (2 * sigma ** 2))

# Function to find and fit peaks
def fit_peaks(signal, height=None, distance=None, prominence=None, width=None):
    # Find peaks
    peaks, properties = find_peaks(signal, height=height, distance=distance, prominence=prominence, width=width)
    
    fitted_peaks = []

    for peak in peaks:
        # Define a small window around the peak for fitting
        window_size = 20  # You can adjust this based on your signal
        start = max(0, peak - window_size)
        end = min(len(signal), peak + window_size)
        x_data = np.arange(start, end)
        y_data = signal[start:end]

        # Initial guesses for Gaussian parameters
        initial_guess = [signal[peak], peak, 3.0]  # [amplitude, mean, stddev]

        try:
            popt, pcov = curve_fit(gaussian, x_data, y_data, p0=initial_guess)
            fitted_peaks.append({
                'center': popt[1],
                'amplitude': popt[0],
                'sigma': popt[2],
                'fwhm': 2 * np.sqrt(2 * np.log(2)) * popt[2]  # FWHM formula for Gaussian
            })

        
        except RuntimeError:
            print(f"Could not fit a peak at index {peak}")


    return fitted_peaks

class Find_Peak(_ACFExperiment):

    def build(self): 
        
        self.setup(sequences)

        self.setup_fit(fitting_func ,'Lorentzian', 218)

        self.setattr_argument("x_axis", EnumerationValue(["frequencies_MHz", "rabi_t"], default="frequencies_MHz"))

        self.setattr_argument("y_axis", EnumerationValue(["pmt_counts_avg", "pmt_counts_avg_thresholded"], default="pmt_counts_avg_thresholded"))

    def prepare(self):

        self.x_axis_data=self.get_dataset(self.x_axis)
        self.y_axis_data=self.get_dataset(self.y_axis)


        self.experiment_data.set_list_dataset(self.y_axis, len(self.x_axis_data), broadcast=True)
        self.experiment_data.set_list_dataset(self.x_axis, len(self.x_axis_data), broadcast=True)
    
        self.fitting_func.setup(len(self.x_axis_data))

        self.experiment_data.enable_experiment_monitor(
            self.y_axis,
            x_data_name=self.x_axis,
            pen=False,
            fit_data_name='fit_signal'
        )
    
    @kernel
    def run(self):

        for i in range(len(self.x_axis_data)):
            self.experiment_data.append_list_dataset(self.x_axis, self.x_axis_data[i])
            self.experiment_data.append_list_dataset(self.y_axis, self.y_axis_data[i])


    def analyze(self):        
        self.fitting_func.fit(self.x_axis_data, self.y_axis_data)


    
    
