from acf.experiment import _ACFExperiment
from acf_sequences.sequences import sequences
from acf_config.arguments_definition import argument_manager
from acf.utils import get_config_dir
from artiq.experiment import *

from acf.function.fitting import *

from scipy.interpolate import interp1d
from awg_utils.transmitter import send_exp_para
from utils_func.stark_D import *
import time

class test_power_tracker(_ACFExperiment):

    def build(self): 
        
        self.setup(sequences)

        #setup sequences
        self.seq.doppler_cool.add_arguments_to_gui()
        self.seq.sideband_cool_2mode.add_arguments_to_gui()
        self.seq.repump_854.add_arguments_to_gui()
        self.seq.readout_397.add_arguments_to_gui()
        self.seq.ion_store.add_arguments_to_gui()

        self.seq.adjust_729_power.build()

    

    def prepare(self):
       
        # Create datasets
        self.num_samples = 2000
        #self.experiment_data.set_list_dataset("pos", num_samples, broadcast=True)
        self.experiment_data.set_list_dataset("att_729_dp", self.num_samples, broadcast=True)
        self.experiment_data.set_list_dataset("time", self.num_samples, broadcast=True)
        #self.experiment_data.set_list_dataset('fit_signal', num_freq_samples, broadcast=True)

        # Enable live plotting
        self.experiment_data.enable_experiment_monitor(
            "att_729_dp",
            x_data_name="time",
            pen=False
        )  

    @kernel
    def run(self):

        print("Running the script")
        self.setup_run()
        self.seq.ion_store.run()
        delay(50*us)

        self.seq.adjust_729_power.init_sampler()

        amp_729_now=0.8
        target_volt=self.seq.adjust_729_power.get_volt(amp_729_now)
        print(target_volt)


        # att_729_now=20.45*dB
        # target_volt=self.seq.adjust_729_power.get_volt(att_729_now)
        # print(target_volt)
        # delay(200*ms)
        # target_volt=self.seq.adjust_729_power.get_volt(att_729_now)

        i=0
        while i < self.num_samples:
            
            delay(1*ms)

            amp_729_new=self.seq.adjust_729_power.run(amp_729_now, target_volt=target_volt)

            self.core.break_realtime()

            volt_now=self.seq.adjust_729_power.get_volt(amp_729_new)

            
            print(volt_now, target_volt,  amp_729_now, amp_729_new)
            amp_729_now=amp_729_new
            self.core.break_realtime()
            

            self.experiment_data.append_list_dataset("att_729_dp", volt_now)
            self.experiment_data.append_list_dataset("time", i)

            time.sleep(0.5)
            
            i=i+1
            self.core.break_realtime()

        self.seq.ion_store.run()
        delay(5*us)
