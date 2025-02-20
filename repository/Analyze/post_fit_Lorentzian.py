from acf.experiment import _ACFExperiment
from acf_sequences.sequences import sequences
from acf_config.arguments_definition import argument_manager

from artiq.experiment import *

from acf.function.fitting import *


class Post_Fit_Lorentzian(_ACFExperiment):

    def build(self): 
        
        self.setup(sequences)

        self.setattr_argument("enable_custom_range", BooleanValue(False),group= "Range")
        self.setattr_argument(
            "min_x",
            NumberValue(default=-999, precision=6),
            group= "Range"
        )
        self.setattr_argument(
            "max_x",
            NumberValue(default=-999, precision=6),
            group= "Range"
        )


        self.setattr_argument(
            "guess_peak",
            NumberValue(default=-999, precision=6)
        )
        self.setattr_argument(
            "guess_amplitude",
            NumberValue(default=-999, precision=6)
        )        
        self.setattr_argument(
            "guess_width",
            NumberValue(default=-999, precision=6)
        )    
        self.setattr_argument(
            "guess_offset",
            NumberValue(default=-999, precision=6)
        )    

        self.setattr_argument("x_axis", EnumerationValue(["frequencies_MHz", "rabi_t"], default="frequencies_MHz"))
        self.setattr_argument("y_axis", EnumerationValue(["pmt_counts_avg", "pmt_counts_avg_thresholded"], default="pmt_counts_avg_thresholded"))

    def prepare(self):


        self.x_axis_data=self.get_dataset(self.x_axis)
        self.y_axis_data=self.get_dataset(self.y_axis)

        
        self.experiment_data.set_list_dataset("fit_x", len(self.x_axis_data), broadcast=True)
        self.experiment_data.set_list_dataset("fit_y", len(self.x_axis_data), broadcast=True)

        self.experiment_data.enable_experiment_monitor(
            "fit_y",
            x_data_name="fit_x",
            pen=False,
            fit_data_name='fit_signal'
        )
    
    @kernel
    def run(self):

        for i in range(len(self.x_axis_data)):
            self.experiment_data.append_list_dataset("fit_x", self.x_axis_data[i])
            self.experiment_data.append_list_dataset("fit_y", self.y_axis_data[i])


    def analyze(self):

        if np.abs(self.guess_peak+999)<1e-5:
            guess_peak=None
        else:
            guess_peak=self.guess_peak

        if np.abs(self.guess_amplitude+999)<1e-5:
            guess_amplitude=None
        else:
            guess_amplitude=self.guess_amplitude

        if np.abs(self.guess_width+999)<1e-5:
            guess_width=None
        else:
            guess_width=self.guess_width

        if np.abs(self.guess_offset+999)<1e-5:
            guess_offset =None
        else:
            guess_offset =self.guess_offset 

        if self.enable_custom_range:
            mask = (self.x_axis_data >= self.min_x) & (self.x_axis_data <= self.max_x)
            fit_x_data=self.x_axis_data[mask]
            fit_y_data=self.y_axis_data[mask]
        else:
            fit_x_data=self.x_axis_data
            fit_y_data=self.y_axis_data

        is_success, fitted_array= find_peak_lorentzian(
            fit_x_data,
            fit_y_data,
            guess_peak=guess_peak, 
            guess_amplitude=guess_amplitude, 
            guess_width=guess_width, 
            guess_offset=guess_offset  
        )

        if self.enable_custom_range:
            fitted_array_full=np.zeros((len(self.x_axis_data)))
            fitted_array_full[mask]=fitted_array
        else:
            fitted_array_full=fitted_array

        self.set_dataset('fit_signal', fitted_array_full, broadcast=True)



    
    
