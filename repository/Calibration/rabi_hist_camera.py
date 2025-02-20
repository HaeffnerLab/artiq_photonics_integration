from artiq.experiment import *
from acf.experiment import _ACFExperiment
from acf_config.arguments_definition import argument_manager

from acf_sequences.sequences import sequences

import numpy as np

from utils_func.otsu import otsu_threshold_manual, kapur_entropy_thresholding


class HistScan_Cam(_ACFExperiment):

    def build(self):
        self.setup(sequences)

        self.seq.doppler_cool.add_arguments_to_gui()
        self.seq.ion_store.add_arguments_to_gui()
    	
        self.seq.cam_two_ions.build()

        self.setattr_argument(
            "samples",
            NumberValue(default=3000, precision=0, step=1),
        )
        self.setattr_argument(
            "bin_width",
            NumberValue(default=1, precision=0, step=1),
        )

        self.setattr_argument(
            "bin_val_max",
            NumberValue(default=550, precision=0, step=1),
        )
        self.setattr_argument(
            "bin_val_min",
            NumberValue(default=250, precision=0, step=1),
        )

        self.setattr_argument("enable_866_off_mode", BooleanValue(False))

    def prepare(self):

        # Create datasets
        if self.enable_866_off_mode:
            self.experiment_data.set_list_dataset("pmt_counts0", self.samples*2, broadcast=True)
            self.experiment_data.set_list_dataset("pmt_counts1", self.samples*2, broadcast=True)
            self.experiment_data.set_list_dataset("index", self.samples*2, broadcast=True)
        else:
            self.experiment_data.set_list_dataset("pmt_counts0", self.samples, broadcast=True)
            self.experiment_data.set_list_dataset("pmt_counts1", self.samples, broadcast=True)
            self.experiment_data.set_list_dataset("index", self.samples, broadcast=True)   

        # Create datasets
        self.num_bins = int((self.bin_val_max-self.bin_val_min) / self.bin_width) + 1
        self.hist_counts0 = [0] * self.num_bins
        self.hist_counts1 = [0] * self.num_bins

        # Start value of each bin
        self.experiment_data.set_list_dataset("rabi_hist_bins", self.num_bins + 1, broadcast=True)
        for bin_i in range(self.num_bins + 1):
            self.experiment_data.append_list_dataset("rabi_hist_bins", bin_i * self.bin_width+self.bin_val_min)

        # Number of counts in each bin
        self.experiment_data.set_list_dataset("rabi_hist_counts0", self.num_bins, broadcast=True)
        for i in range(self.num_bins):
            self.experiment_data.append_list_dataset("rabi_hist_counts0", 0)

        self.experiment_data.set_list_dataset("rabi_hist_counts1", self.num_bins, broadcast=True)
        for i in range(self.num_bins):
            self.experiment_data.append_list_dataset("rabi_hist_counts1", 0)

        # self.experiment_data.enable_experiment_monitor(
        #     y_data_name="pmt_counts0",
        #     x_data_name="index"
        # )

    @kernel
    def run(self):
        
        print("Running the script")
        self.setup_run()
        self.seq.ion_store.run()
        delay(5*us)

        self.seq.cam_two_ions.cam_setup()
        

        for i in range(2 if self.enable_866_off_mode else 1):
            sample_num=0
            while sample_num< self.samples:
                
                #line trigger
                # if self.seq.ac_trigger.run(self.core, self.core.seconds_to_mu(25*ms), self.core.seconds_to_mu(50*us) ) <0 : 
                #    continue
                sample_num+=1

                delay(50*us)
            
                # Doppler cooling    
                self.seq.doppler_cool.run()
                delay(5*us)


                cam_input=[0.0,0.0]
                if i==0:
                    self.seq.cam_two_ions.cam_readout_raw(cam_input)
                else:
                    self.seq.cam_two_ions.cam_readout_raw(cam_input, True)
    
                #delay(10*ms)
                num_pmt_pulses0=cam_input[0]*1.0#/ self.cam_ROI_size/ self.cam_ROI_size
                num_pmt_pulses1=cam_input[1]*1.0#/ self.cam_ROI_size/ self.cam_ROI_size

                print(num_pmt_pulses0, num_pmt_pulses1)
                self.core.break_realtime()

                #protect ion
                self.seq.ion_store.run()
                delay(5*us)

                self.experiment_data.append_list_dataset("pmt_counts0",num_pmt_pulses0)
                self.experiment_data.append_list_dataset("pmt_counts1",num_pmt_pulses1)
                self.experiment_data.append_list_dataset("index",sample_num+i*self.samples)


                for bin_i in range(self.num_bins - 1):

                    
                    if bin_i * self.bin_width < num_pmt_pulses0-self.bin_val_min <= (bin_i + 1) * self.bin_width:
                        
                        self.hist_counts0[bin_i] += 1
                        self.experiment_data.insert_nd_dataset("rabi_hist_counts0", bin_i, self.hist_counts0[bin_i])
                        break

                for bin_i in range(self.num_bins - 1):
                    if bin_i * self.bin_width<num_pmt_pulses1-self.bin_val_min <= (bin_i + 1) * self.bin_width:
                        self.hist_counts1[bin_i] += 1
                        self.experiment_data.insert_nd_dataset("rabi_hist_counts1", bin_i, self.hist_counts1[bin_i])
                        break

                self.core.break_realtime()
                
            # if i == 0:
            #     print("CONTINUING IN 1 SECONDS")
            #     delay(1*s)
        
        #protect ion
        self.seq.ion_store.run()
        delay(5*us)
    def analyze(self):
        

        
        try:
            data1=self.get_dataset("pmt_counts1")
            # Apply Otsu's thresholding using OpenCV 4
            binary1= otsu_threshold_manual(data1) #otsu_threshold_manual(data1, 1390)
            print("Threshold0: ", binary1)
            self.parameter_manager.set_param(
                "readout/cam_threshold1",
                binary1
            )
        except Exception:
            print("Failed to find threshold 1")

        try:
            data0=self.get_dataset("pmt_counts0")
            # Apply Otsu's thresholding using OpenCV 4
            binary0= otsu_threshold_manual(data0)
            print("Threshold0: ", binary0)
            self.parameter_manager.set_param(
                "readout/cam_threshold0",
                binary0
            )
        except Exception:
            print("Failed to find threshold 0")
        