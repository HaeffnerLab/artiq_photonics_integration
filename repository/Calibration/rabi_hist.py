from artiq.experiment import *
from acf.experiment import _ACFExperiment
from acf_config.arguments_definition import argument_manager

from acf_sequences.sequences import sequences

import numpy as np
from utils_func.otsu import otsu_threshold_manual

class HistScan(_ACFExperiment):

    def build(self):
        self.setup(sequences)

        self.seq.doppler_cool.add_arguments_to_gui()
        self.seq.sideband_cool.add_arguments_to_gui()
        self.seq.ion_store.add_arguments_to_gui()
    	
        self.seq.readout_397.add_arguments_to_gui()


        self.setattr_argument(
            "samples",
            NumberValue(default=1000, precision=0, step=1),
        )

        self.setattr_argument(
            "bin_width",
            NumberValue(default=1, precision=0, step=1),
        )

        self.setattr_argument(
            "bin_val_max",
            NumberValue(default=2000, precision=0, step=1),
        )

        self.setattr_argument("enable_sideband_cool", BooleanValue(False))



    def prepare(self):

        # Create datasets
        self.num_bins = int(self.bin_val_max / self.bin_width) + 1
        self.hist_counts = [0] * self.num_bins
        self.raw_data=[0]*(self.samples*2)

        # Start value of each bin
        self.experiment_data.set_list_dataset("rabi_hist_bins", self.num_bins + 1, broadcast=True)
        for bin_i in range(self.num_bins + 1):
            self.experiment_data.append_list_dataset("rabi_hist_bins", bin_i * self.bin_width)

        # Number of counts in each bin
        self.experiment_data.set_list_dataset("rabi_hist_counts", self.num_bins, broadcast=True)
        for i in range(self.num_bins):
            self.experiment_data.append_list_dataset("rabi_hist_counts", 0)


    @kernel
    def run(self):
        
        print("Running the script")
        self.setup_run()
        self.seq.ion_store.run()
        delay(5*us)


        for i in range(2):
            sample_num=0
            while sample_num< self.samples:

                #line trigger
                # if self.seq.ac_trigger.run(self.core, self.core.seconds_to_mu(5*ms), self.core.seconds_to_mu(50*us) ) <0 : 
                #    continue
                sample_num+=1

                delay(50*us)

                # Doppler cooling    
                self.seq.doppler_cool.run()
                delay(50*us)

                # Doppler cooling    
                if self.enable_sideband_cool:
                    self.seq.sideband_cool.run()

                # Detection
                num_pmt_pulses = self.seq.readout_397.run(turn_off_866=(True if i==1 else False))


                #protect ion
                self.seq.ion_store.run()
                delay(5*us)


                for bin_i in range(self.num_bins - 1):
                    
                    if num_pmt_pulses < (bin_i + 1) * self.bin_width:
                        self.hist_counts[bin_i] += 1
                        self.experiment_data.insert_nd_dataset("rabi_hist_counts", bin_i, self.hist_counts[bin_i])
                        break

                self.raw_data[i*self.samples+sample_num-1]=num_pmt_pulses
                
                delay(8*ms)
                
               
            
            if i == 0:
                print("CONTINUING IN 1 SECONDS")
                delay(1*s)
        
        #protect ion
        self.seq.ion_store.run()
        delay(5*us)

        #print("QIMING PLEASE THROW OUT THE IONS, THE WORLD DEPENDS ON YOUUUU") From David Miron
    def analyze(self):
    
        try:
            # Apply Otsu's thresholding using OpenCV 4
            binary = otsu_threshold_manual(self.raw_data)

            self.experiment_data.set_list_dataset("threshold", 1, broadcast=True)
            self.experiment_data.append_list_dataset("threshold", binary)

            print("Threshold: ", binary)

            self.parameter_manager.set_param(
                "readout/threshold",
                binary
            )
        except Exception:
            print("Failed to find threshold")
        
        
