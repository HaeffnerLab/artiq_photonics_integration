from acf.experiment import _ACFExperiment
from acf_sequences.sequences import sequences
from acf_config.arguments_definition import argument_manager

from artiq.experiment import *

from acf.function.fitting import *

class Post_Fit(_ACFExperiment):

    def build(self): 
        
        self.setup(sequences)

        self.setup_fit(fitting_func, 'Sin' ,-1)

        self.setattr_argument(
            "min_x",
            NumberValue(default=-999, precision=6)
        )
        self.setattr_argument(
            "max_x",
            NumberValue(default=-999, precision=6)
        )

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


    
    
