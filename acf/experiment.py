from artiq.experiment import EnvExperiment, kernel, NumberValue
from acf.hardware_setup import HardwareSetup
from acf.experiment_data import ExperimentData
from acf.parameter_manager import ParameterManager

# from awg_utils.rf_modulator import rf_modulator

class _ACFExperiment(EnvExperiment):

    def setup(self, sequences):
        """Setup the experiment class.

        Args:
            seq (SequencesContainer): Container for all sequences.
        """
        self.hardware = HardwareSetup()
        self.hardware.initialize(self)

        self.experiment_data = ExperimentData(self)
        self.parameter_manager = ParameterManager(self)

        self.init_sequences(sequences)

    
    def setup_fit(self, fitting_func, default_func, default_arg):
        self.fitting_func=fitting_func
        self.fitting_func.initialize(self, default_func, default_arg)

    @kernel
    def setup_run(self):
        """Setup to run at the beginning of the run method."""
        self.core.reset()
        self.core.break_realtime()


        # Init all DDSs
        for dds in self.hardware.get_all_dds():
           dds.init()
           dds.cpld.init()
        
        # Init all devices / turn off all devices / set them to initial value

        self.seq.ion_store.run()
        #self.seq.init_device.run()
        

        self.core.break_realtime()

    def init_sequences(self, sequences):
        """Set up the sequences.

        Args:
            sequences (SequencesContainer): The sequences container.
        """
        self.seq = sequences
        for sequence in self.seq.all_sequences:
            sequence.initialize(self, self.seq, self.hardware)

    def build_sequences(self):
        for sequence in self.seq.all_sequences:
            sequence.build()
        

    def add_arg_from_param(self, param, min_value=None, max_value=None):
        """Add an argument who's default value comes from a stored parameter.

        Args:
            param (str): The name of the parameter.
            min_value (float): Minimum value of the parameter.
            max_value (float): Maximum value of the parameter.
        """
        self.setattr_argument(
            param,
            NumberValue(
                default=self.parameter_manager.get_param(param),
                unit=self.parameter_manager.get_param_units(param),
                precision=5,
                min=min_value,
                max=max_value
            ),
            group="System Parameters",
        )

        # Set attribute manually because of forward slashes in parameter names
        setattr(self, param.replace("/", "_"), getattr(self, param))


