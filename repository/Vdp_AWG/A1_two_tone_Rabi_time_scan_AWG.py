from acf.experiment import _ACFExperiment
from acf_sequences.sequences import sequences
from acf_config.arguments_definition import argument_manager
from acf.utils import get_config_dir
from artiq.experiment import *

from acf.function.fitting import *

from scipy.interpolate import interp1d


from awg_utils.transmitter import send_exp_para

class A1_two_tone_Rabi_time_scan_AWG(_ACFExperiment):

    def build(self): 
        
        self.setup(sequences)

        self.seq.sideband_cool.add_arguments_to_gui()
        self.seq.op_pump.add_arguments_to_gui()

        self.seq.doppler_cool.add_arguments_to_gui()
        self.seq.repump_854.add_arguments_to_gui()
        self.seq.readout_397.add_arguments_to_gui()
        self.seq.ion_store.add_arguments_to_gui()

        self.setup_fit(fitting_func, 'Sin' ,-1)
        

        # self.add_arg_from_param("frequency/729_sp")
        # self.add_arg_from_param("attenuation/729_sp")



        self.setattr_argument(
            "scan_rabi_t",
            Scannable(
                default=RangeScan(
                    start=0*us,
                    stop=100*us,
                    npoints=100
                ),
                global_min=0*us,
                global_max=10000*us,
                global_step=10*us,
                unit="us"
            ),
            tooltip="Scan parameter for sweeping the 729 double pass on time."
        )
	
        self.setattr_argument(
            "freq_729_dp",
            NumberValue(default=self.parameter_manager.get_param("qubit/Sm1_2_Dm5_2"), min=200*MHz, max=250*MHz, unit="MHz", precision=8),
            tooltip="729 double pass frequency",
        )


        self.setattr_argument("enable_dp_freq_compensation", BooleanValue(True))
        self.setattr_argument(
            "att_729_dp",
            NumberValue(default=self.parameter_manager.get_param("attenuation/729_dp"), min=10*dB, max=30*dB, unit="dB", precision=8),
            tooltip="729 double pass attenuation"
        )

        self.setattr_argument(
            "freq_729_sp",
            NumberValue(default=self.parameter_manager.get_param("frequency/729_sp")-2*self.parameter_manager.get_param("qubit/vib_freq"), min=20*MHz, max=250*MHz, unit="MHz", precision=8),
            tooltip="729 double pass frequency",
        )

        self.setattr_argument(
            "freq_729_sp_aux",
            NumberValue(default=self.parameter_manager.get_param("frequency/729_sp")+2*self.parameter_manager.get_param("qubit/vib_freq"), min=20*MHz, max=250*MHz, unit="MHz", precision=8),
            tooltip="729 double pass frequency",
        )


        self.setattr_argument(
            "amp_729_sp",
            NumberValue(default=self.parameter_manager.get_param("SDF/amp_729_sp"), min=1e-7, max=0.8, precision=8),
            tooltip="729 single pass attenuation"
        )
        
        self.setattr_argument(
            "amp_729_sp_aux",
            NumberValue(default=self.parameter_manager.get_param("SDF/amp_729_sp_aux"), min=1e-7, max=0.8, precision=8),
            tooltip="729 single pass attenuation"
        )

        self.setattr_argument(
            "samples_per_time",
            NumberValue(default=50, precision=0, step=1),
            tooltip="Number of samples to take for each time",
        )

        self.setattr_argument("enable_sideband_cool", BooleanValue(True))
        self.setattr_argument("enable_thresholding", BooleanValue(True))
        
        self.setattr_argument(
            "threshold_pmt_count",
            NumberValue(default=self.parameter_manager.get_param("readout/threshold"), precision=8),
            tooltip="Threshold PMT counts",
        )    


    def prepare(self):
        self.fitting_func.setup(len(self.scan_rabi_t.sequence))
        # Create datasets
        num_freq_samples = len(self.scan_rabi_t.sequence)
        # self.experiment_data.set_nd_dataset("pmt_counts", [num_freq_samples, self.samples_per_time])
        self.experiment_data.set_list_dataset("pmt_counts_avg_thresholded", num_freq_samples, broadcast=True)
        self.experiment_data.set_list_dataset("rabi_t", num_freq_samples, broadcast=True)
        self.experiment_data.set_list_dataset('fit_signal', num_freq_samples, broadcast=True)

        # Enable live plotting
        self.experiment_data.enable_experiment_monitor(
            "pmt_counts_avg_thresholded",
            x_data_name="rabi_t",
            pen=False,
            fit_data_name='fit_signal'
        )
        if self.enable_dp_freq_compensation:
            self.setup_dp_att()


    def setup_dp_att(self):

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

        # Create the interpolation function
        interpolation_function = interp1d(freq_data, att_data, fill_value="extrapolate", kind='linear')

        self.att_729_dp =  float(interpolation_function(self.freq_729_dp/MHz))*dB

        print(self.att_729_dp)

    @rpc
    def send_exp_para(
        self,
        freq_RSB,
        freq_BSB,
        amp_RSB,
        amp_BSB   
    ):
        send_exp_para(["SDF", {
                "freq_sp_RSB":   freq_RSB,
                "freq_sp_BSB":   freq_BSB,
                "amp_sp_RSB":  amp_RSB,
                "amp_sp_BSB":   amp_BSB,
                "num_loop":max(self.samples_per_time+100,100)
            }])  

    @kernel
    def rabi_AWG(self,pulse_time, freq_729_dp, att_729_dp):
        
        #double pass 
        self.dds_729_dp.set(freq_729_dp)
        self.dds_729_dp.set_att(att_729_dp)

        
        self.ttl_rf_switch_AWG_729SP.on()
        self.ttl_rf_switch_DDS_729SP.off()
        self.ttl_awg_trigger.pulse(1*us)
            
        self.dds_729_sp.sw.off()
        self.dds_729_dp.sw.on()
        delay(pulse_time)
        self.dds_729_dp.sw.off()

        self.ttl_awg_trigger.pulse(1*us)
        self.ttl_rf_switch_AWG_729SP.off()
        self.ttl_rf_switch_DDS_729SP.on()

    @kernel
    def run(self):
        print("Running the script")
        self.setup_run()
        self.seq.ion_store.run()

        delay(50*us)
        for time_i in range(len(self.scan_rabi_t.sequence)): 
            total_thresh_count = 0
            total_pmt_counts = 0
            sample_num=0
            rabi_t = self.scan_rabi_t.sequence[time_i]
            delay(200*us)
            self.seq.ion_store.run()
            self.send_exp_para(self.freq_729_sp_aux, self.freq_729_sp,self.amp_729_sp_aux,self.amp_729_sp)   
            delay(25*ms)

            while sample_num<self.samples_per_time:
                #line trigger
                if self.seq.ac_trigger.run(self.core, self.core.seconds_to_mu(20*ms), self.core.seconds_to_mu(50*us) ) <0 : 
                    continue
                sample_num+=1
                delay(50*us)
                self.seq.off_dds.run()
                self.seq.repump_854.run()
                #  Cool
                self.seq.doppler_cool.run()

                if self.enable_sideband_cool:
                    self.seq.sideband_cool.run()
                else:
                    self.seq.op_pump.run()
                delay(5*us)
                

                self.rabi_AWG(rabi_t, self.freq_729_dp, self.att_729_dp)

                #read out
                num_pmt_pulses=self.seq.readout_397.run()

                # 854 repump
                self.seq.repump_854.run()
                #protect ion
                self.seq.ion_store.run()
                delay(20*us)

                # Update dataset
                # self.experiment_data.insert_nd_dataset("pmt_counts",
                #                             [time_i, sample_num],
                #                             num_pmt_pulses)
                
                if num_pmt_pulses < self.threshold_pmt_count:
                    total_thresh_count += 1

                total_pmt_counts += num_pmt_pulses

                delay(1*ms)
            
            self.experiment_data.append_list_dataset("rabi_t", rabi_t / us)

            if self.enable_thresholding:
                self.experiment_data.append_list_dataset("pmt_counts_avg_thresholded",
                                          float(total_thresh_count) / self.samples_per_time)
            else:
                self.experiment_data.append_list_dataset("pmt_counts_avg_thresholded",
                                          float(total_pmt_counts) / self.samples_per_time)
            delay(5*ms)

        self.seq.ion_store.run()
    
    def analyze(self):
        rabi_time=self.get_dataset("rabi_t")
        rabi_PMT=self.get_dataset('pmt_counts_avg_thresholded')
        self.fitting_func.fit(rabi_time, rabi_PMT)


    
    
