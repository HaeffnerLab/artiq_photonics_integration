

# calibrate for bichromatic light

# configuration 1
#                   frequency                            attenuation
# double pass:      line_freq+vib                        att1
# single pass:      default_sp+vib*2 default_sp-vib*2    default attenuation

# configuration 2
# double pass:      line_freq-vib                        att2
# single pass:      default_sp+vib*2 default_sp-vib*2    default attenuation

# step 1:
# single tone, manually change double pass frequency between line_freq+vib & line_freq-vib
# measure power with photodiode to balance power between these two frequencies

# step 2:
# do the two configuration measurement

from acf.experiment import _ACFExperiment
from acf_sequences.sequences import sequences
from acf_config.arguments_definition import argument_manager
from acf.utils import get_config_dir

from artiq.experiment import *

from acf.function.fitting import *


from scipy.interpolate import interp1d

class A1_two_tone_Rabi_freq_scan_dp(_ACFExperiment):

    def build(self): 
        
        self.setup(sequences)

        self.seq.sideband_cool.add_arguments_to_gui()
        self.seq.doppler_cool.add_arguments_to_gui()
        self.seq.repump_854.add_arguments_to_gui()
        self.seq.readout_397.add_arguments_to_gui()
        self.seq.ion_store.add_arguments_to_gui()

        # self.setup_fit(fitting_func, 'Sin' ,-1)
        
        # self.add_arg_from_param("frequency/397_resonance")
        # self.add_arg_from_param("frequency/397_cooling")
        # self.add_arg_from_param("frequency/397_far_detuned")
        # self.add_arg_from_param("frequency/866_cooling")
        # self.add_arg_from_param("frequency/854_dp")

        # self.add_arg_from_param("attenuation/397")
        # self.add_arg_from_param("attenuation/397_far_detuned")
        # self.add_arg_from_param("attenuation/866")
        # self.add_arg_from_param("attenuation/854_dp")

        self.setattr_argument(
            "freq_729_sp",
            NumberValue(default=80*MHz-2*self.parameter_manager.get_param("qubit/vib_freq"), min=20*MHz, max=250*MHz, unit="MHz", precision=8),
            tooltip="729 double pass frequency",
        )

        self.setattr_argument(
            "freq_729_sp_aux",
            NumberValue(default=80*MHz+2*self.parameter_manager.get_param("qubit/vib_freq"), min=20*MHz, max=250*MHz, unit="MHz", precision=8),
            tooltip="729 double pass frequency",
        )

        self.setattr_argument(
            "att_729_sp",
            NumberValue(default=self.parameter_manager.get_param("attenuation/729_sp"), min=10*dB, max=30*dB, unit="dB", precision=8),
            tooltip="729 single pass attenuation"
        )
        
        self.setattr_argument(
            "att_729_sp_aux",
            NumberValue(default=self.parameter_manager.get_param("attenuation/729_sp"), min=10*dB, max=30*dB, unit="dB", precision=8),
            tooltip="729 single pass attenuation"
        )

        self.setattr_argument(
            "samples_per_time",
            NumberValue(default=50, precision=0, step=1),
            tooltip="Number of samples to take for each time",
        )

        self.setattr_argument("enable_thresholding", BooleanValue(True))
        self.setattr_argument(
            "threshold_pmt_count",
            NumberValue(default=self.parameter_manager.get_param("readout/threshold"), precision=8),
            tooltip="Threshold PMT counts",
        )    

        self.setattr_argument(
            "rabi_t",
            NumberValue(default=7.34*us, min=0*us, max=5*ms, unit="us",precision=6)
        )

        self.setattr_argument(
            "scan_freq_729_dp",
            Scannable(
                default=RangeScan(
                    start=self.parameter_manager.get_param("qubit/Sm1_2_Dm5_2")-20*kHz,
                    stop=self.parameter_manager.get_param("qubit/Sm1_2_Dm5_2")+20*kHz,
                    npoints=100
                ),
                global_min=150*MHz,
                global_max=250*MHz,
                global_step=1*kHz,
                unit="MHz",
                precision=6
            ),
            tooltip="Scan parameter for sweeping the 729 double pass laser."
        )

    def prepare(self):
        # self.fitting_func.setup(len(self.scan_rabi_t.sequence))
        # Create datasets
        num_freq_samples = len(self.scan_freq_729_dp.sequence)
        self.experiment_data.set_nd_dataset("pmt_counts", [num_freq_samples, self.samples_per_time], broadcast=True)
        self.experiment_data.set_list_dataset("pmt_counts_avg_thresholded", num_freq_samples, broadcast=True)
        self.experiment_data.set_list_dataset("frequencies_MHz", num_freq_samples, broadcast=True)

        # Enable live plotting
        self.experiment_data.enable_experiment_monitor(
            "pmt_counts_avg_thresholded",
            x_data_name="frequencies_MHz",
            pen=False
        )

        self.setup_dp_att()

    def setup_dp_att(self):
        num_freq_samples = len(self.scan_freq_729_dp.sequence)
        self.att_seq = [0.0]*num_freq_samples

        # Initialize empty lists to store x and y values
        freq_data =[]
        att_data = []
        # Read the file and parse each line
        with open(get_config_dir()/'../repository/Vdp/freq_att.txt', 'r') as f:
            for line in f:
               
                # Split the line by the comma and strip any extra whitespace
                x_val, y_val = line.strip().split(', ')
                freq_data.append(float(x_val))  # Convert x value to int
                att_data.append(float(y_val))  # Convert y value to float

        print(freq_data[0], freq_data[1])
        print(att_data[0], att_data[-1])

        # Create the interpolation function
        interpolation_function = interp1d(freq_data, att_data, fill_value="extrapolate", kind='linear')

        for i in range(num_freq_samples):
            # Interpolate to find the corresponding x value for fx1
             self.att_seq[i]= float(interpolation_function(self.scan_freq_729_dp.sequence[i]/MHz))*dB



    @kernel
    def run(self):
        print("Running the script")
        self.setup_run()

        self.seq.ion_store.run()
        delay(50*us)
        
        for freq_i in range(len(self.scan_freq_729_dp.sequence)):
            freq_729_dp=self.scan_freq_729_dp.sequence[freq_i]
            total_thresh_count = 0
            total_pmt_counts = 0
            sample_num=0

            self.seq.ion_store.run()
            delay(200*us)

            while sample_num<self.samples_per_time:

                #line trigger
                if self.seq.ac_trigger.run(self.core, self.core.seconds_to_mu(5*ms), self.core.seconds_to_mu(50*us) ) <0 : 
                    continue
                sample_num+=1
                delay(50*us)
                
                self.seq.repump_854.run()
                #  Cool
                self.seq.doppler_cool.run()
                self.seq.sideband_cool.run()

                #set 729nm light data
                self.dds_729_dp.set(freq_729_dp)
                self.dds_729_dp.set_att(self.att_seq[freq_i])

                self.dds_729_sp.set(self.freq_729_sp)
                self.dds_729_sp_aux.set(self.freq_729_sp_aux)
                self.dds_729_sp.set_att(self.att_729_sp)
                self.dds_729_sp_aux.set_att(self.att_729_sp_aux)
                delay(5*us)

                # Attempt Rabi flop
                self.dds_729_dp.sw.on()
                self.dds_729_sp.sw.on()
                self.dds_729_sp_aux.sw.on()
                delay(self.rabi_t)
                self.dds_729_dp.sw.off()
                #self.dds_729_sp.sw.off()

                delay(10*us)

                num_pmt_pulses=self.seq.readout_397.run()

                delay(5*us)

                #protect ion
                self.seq.repump_854.run()
                self.seq.ion_store.run()

                # Update dataset
                self.experiment_data.insert_nd_dataset("pmt_counts",
                                            [freq_i, sample_num],
                                            num_pmt_pulses)
                
                if num_pmt_pulses < self.threshold_pmt_count:
                    total_thresh_count += 1

                total_pmt_counts += num_pmt_pulses

                delay(1*ms)
            
            self.experiment_data.append_list_dataset("frequencies_MHz", freq_729_dp / MHz)
            if self.enable_thresholding:
                self.experiment_data.append_list_dataset("pmt_counts_avg_thresholded",
                                          float(total_thresh_count) / self.samples_per_time)
            else:
                self.experiment_data.append_list_dataset("pmt_counts_avg_thresholded",
                                          float(total_pmt_counts) / self.samples_per_time)
            delay(5*ms)

        self.seq.ion_store.run()
    
    # def analyze(self):
    #     rabi_time=self.get_dataset("rabi_t")
    #     rabi_PMT=self.get_dataset('pmt_counts_avg_thresholded')
    #     self.fitting_func.fit(rabi_time, rabi_PMT)


    
    
