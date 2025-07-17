

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

class A2_Displace_Wigner_1D(_ACFExperiment):

    def build(self): 
        
        self.setup(sequences)

        self.seq.sideband_cool.add_arguments_to_gui()
        self.seq.doppler_cool.add_arguments_to_gui()
        self.seq.repump_854.add_arguments_to_gui()
        self.seq.readout_397.add_arguments_to_gui()
        self.seq.ion_store.add_arguments_to_gui()

        self.setup_fit(fitting_func, 'Sin' ,-1)
        
        # self.add_arg_from_param("frequency/397_resonance")
        # self.add_arg_from_param("frequency/397_cooling")
        # self.add_arg_from_param("frequency/397_far_detuned")
        # self.add_arg_from_param("frequency/866_cooling")


        self.add_arg_from_param("frequency/729_sp")
        self.add_arg_from_param("attenuation/729_sp")

        self.setattr_argument("enable_rot_pulse", BooleanValue(False), group='rotation pulse excitation')
        self.setattr_argument(
            "freq_729_dp_rot",
            NumberValue(default=self.parameter_manager.get_param("qubit/Sm1_2_Dm1_2"), min=200*MHz, max=250*MHz, unit="MHz", precision=8),
            tooltip="729 double pass frequency for resonance",
            group='rotation pulse excitation'
        )
        self.setattr_argument(
            "att_729_dp_rot",
            NumberValue(default=self.parameter_manager.get_param("attenuation/729_dp"), min=5*dB, max=30*dB, unit="dB", precision=8),
            tooltip="729 double pass amplitude for resonance",
            group='rotation pulse excitation'
        )
        self.setattr_argument(
            "freq_729_sp_rot",
            NumberValue(default=self.parameter_manager.get_param("frequency/729_sp"), min=200*MHz, max=250*MHz, unit="MHz", precision=8),
            tooltip="729 double pass frequency for resonance",
            group='rotation pulse excitation'
        )
        self.setattr_argument(
            "att_729_sp_rot",
            NumberValue(default=self.parameter_manager.get_param("attenuation/729_sp"), min=5*dB, max=30*dB, unit="dB", precision=8),
            tooltip="729 double pass amplitude for resonance",
            group='rotation pulse excitation'
        )
        self.setattr_argument(
            "rot_drive_time",
            NumberValue(default=0.1*us, min=0.*us, max=1000*us, unit='us', precision=8),
            tooltip="Drive time for pi excitation",
            group='rotation pulse excitation'
        )  
      

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
            delay(200*us)

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
                self.seq.sideband_cool.run()
                delay(5*us)


                if self.enable_rot_pulse:
                    self.seq.rabi.run(self.rot_drive_time,
                                  self.freq_729_dp_rot,
                                  self.freq_729_sp_rot,
                                  self.att_729_dp_rot,
                                  self.att_729_sp_rot,
                                  phase = 0.0)
                
                # basis 
                # self.dds_729_dp.set(self.freq_729_dp)
                # self.dds_729_sp.set(self.freq_729_sp,phase = 0.0)
                # self.dds_729_sp_aux.set(self.freq_729_sp_aux, phase=0.0)
                # self.dds_729_sp.set_att(self.att_729_sp)
                # self.dds_729_sp_aux.set_att(self.att_729_sp_aux)
                # self.dds_729_dp.set_att(self.att_729_dp)

                # # Attempt Rabi flop
                # self.dds_729_sp.sw.on()
                # self.dds_729_sp_aux.sw.on()
                # self.dds_729_dp.sw.on()
                # delay(200*us)
                # self.dds_729_dp.sw.off()

                # x basis
                self.seq.displacement.run(200*us,
                    self.att_729_dp, self.att_729_sp, self.att_729_sp_aux,
                    self.freq_729_dp, self.freq_729_sp, self.freq_729_sp_aux,
                    drive_phase_sp = 0.0, drive_phase_sp_aux = 0.5
                )

                self.seq.repump_854.run()

                self.seq.displacement.run(rabi_t,
                     self.att_729_dp, self.att_729_sp, self.att_729_sp_aux,
                     self.freq_729_dp, self.freq_729_sp, self.freq_729_sp_aux,
                     drive_phase_sp = 0.0, drive_phase_sp_aux = 0.5
                )


                # # basis  
                # self.dds_729_dp.set(self.freq_729_dp)
                # self.dds_729_sp.set(self.freq_729_sp,phase = 0.0)
                # self.dds_729_sp_aux.set(self.freq_729_sp_aux, phase=0.36)
                # self.dds_729_sp.set_att(self.att_729_sp)
                # self.dds_729_sp_aux.set_att(self.att_729_sp_aux)
                # self.dds_729_dp.set_att(self.att_729_dp)

                # # Attempt Rabi flop
                # self.dds_729_sp.sw.on()
                # self.dds_729_sp_aux.sw.on()
                # self.dds_729_dp.sw.on()
                # delay(rabi_t)
                # self.dds_729_dp.sw.off()

                '''

                # carrier pi/2

              
                    
                # # self.dds_729_sp.set(80*MHz,phase = 0.5)
                # # self.dds_729_dp.sw.on()
                # # delay(1.6*us)
                # # self.dds_729_dp.sw.off()



                # displacement operator 

                # self.dds_729_dp.set(self.freq_729_dp)
                # self.dds_729_sp.set(self.freq_729_sp,phase = 0.0)
                # self.dds_729_sp_aux.set(self.freq_729_sp_aux, phase=0.0)
                # self.dds_729_sp.set_att(self.att_729_sp)
                # self.dds_729_sp_aux.set_att(self.att_729_sp_aux)
                # self.dds_729_dp.set_att(self.att_729_dp)

                # # Attempt Rabi flop
                # self.dds_729_sp.sw.on()
                # self.dds_729_sp_aux.sw.on()
                # self.dds_729_dp.sw.on()
                # delay(100*us)
                # #delay(10*us)
                # self.dds_729_dp.sw.off()

                # spin reset

                # self.seq.repump_854.run()

                # SDF analysis pulse
                self.dds_729_dp.set(self.freq_729_dp)
                self.dds_729_sp.set(self.freq_729_sp-0.02* MHz,phase = 0.0)
                #self.dds_729_sp.set(80*MHz,phase = 0.0)
                self.dds_729_sp_aux.set(self.freq_729_sp_aux+0.02* MHz, phase=0.5)
                self.dds_729_sp.set_att(self.att_729_sp)
                self.dds_729_sp_aux.set_att(self.att_729_sp_aux)
                self.dds_729_dp.set_att(self.att_729_dp)

                # Attempt Rabi flop
                self.dds_729_sp.sw.on()
                #self.dds_729_sp_aux.sw.on()
                self.dds_729_dp.sw.on()
                delay(rabi_t)
                #delay(10*us)
                self.dds_729_dp.sw.off()
                self.dds_729_sp_aux.sw.off()


                # self.seq.rabi.run(self.rot_drive_time,
                #                 self.freq_729_dp,
                #                 80*MHz,
                #                 self.att_729_dp,
                #                 self.att_729_sp,
                #                 phase = 0.4)

                

                #self.dds_729_sp.sw.off()

                

                # SDF analysis pulse
                self.dds_729_dp.set(self.freq_729_dp)
                self.dds_729_sp.set(self.freq_729_sp,phase = 0.0)
                self.dds_729_sp_aux.set(self.freq_729_sp_aux, phase=0.5)
                self.dds_729_sp.set_att(self.att_729_sp)
                self.dds_729_sp_aux.set_att(self.att_729_sp_aux)
                self.dds_729_dp.set_att(self.att_729_dp)

                # Attempt Rabi flop
                self.dds_729_sp.sw.on()
                self.dds_729_sp_aux.sw.on()
                self.dds_729_dp.sw.on()
                delay(rabi_t)
                #delay(10*us)
                self.dds_729_dp.sw.off()

                '''


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


    
    
