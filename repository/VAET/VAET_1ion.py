from acf.experiment import _ACFExperiment
from acf_sequences.sequences import sequences
from acf_config.arguments_definition import argument_manager
from acf.utils import get_config_dir
from artiq.experiment import *

from acf.function.fitting import *

from scipy.interpolate import interp1d

from artiq.coredevice.ad9910 import PHASE_MODE_ABSOLUTE, PHASE_MODE_CONTINUOUS, PHASE_MODE_TRACKING
from awg_utils.transmitter import send_exp_para

from utils_func.stark_D import stark_shift

class A1_VAET_single_ion(_ACFExperiment):

    def build(self): 
        
        self.setup(sequences)

        self.seq.sideband_cool.add_arguments_to_gui()
        self.seq.doppler_cool.add_arguments_to_gui()
        self.seq.repump_854.add_arguments_to_gui()
        self.seq.readout_397.add_arguments_to_gui()
        self.seq.ion_store.add_arguments_to_gui()

        #rotation Rx(pi/2)


        # rotation
        self.setattr_argument(
            "rot_x_freq_729_sp",
            NumberValue(default=self.parameter_manager.get_param("frequency/729_sp"), min=20*MHz, max=250*MHz, unit="MHz", precision=8),
            tooltip="729 double pass frequency",
            group='Rotation_x'
        )
        self.setattr_argument(
            "rot_x_amp_729_sp",
            NumberValue(default=self.parameter_manager.get_param("AWG_amplitude/729_sp"), min=0, max=1, precision=8),
            tooltip="729 double pass frequency",
            group='Rotation_x'
        )
        self.setattr_argument(
            "rot_time",
            NumberValue(default=self.parameter_manager.get_param("VAET_1ion/rot_time"), min=0, max=100, precision=8, unit='us'),
            tooltip="729 double pass frequency",
            group='Rotation_x'
        )

        # sigma_x sigma_y term
        self.setattr_argument(
            "J_freq_729_sp",
            NumberValue(default=self.parameter_manager.get_param("frequency/729_sp"), min=20*MHz, max=250*MHz, unit="MHz", precision=8),
            tooltip="729 double pass frequency",
            group='sigma'
        )
        self.setattr_argument(
            "Jx_amp_729_sp",
            NumberValue(default=self.parameter_manager.get_param("VAET_1ion/rot_x_amp"), min=0, max=1, precision=8),
            tooltip="729 double pass frequency",
            group='sigma'
        )
        self.setattr_argument(
            "Jy_amp_729_sp",
            NumberValue(default=self.parameter_manager.get_param("VAET_1ion/rot_y_amp"), min=0, max=1, precision=8),
            tooltip="729 double pass frequency",
            group='sigma'
        )

        # SDF
        self.setattr_argument(
            "freq_729_sp_BSB",
            NumberValue(default=80*MHz-2*self.parameter_manager.get_param("qubit/vib_freq"), min=20*MHz, max=250*MHz, unit="MHz", precision=8),
            tooltip="729 double pass frequency",
            group='SDF'
        )
        self.setattr_argument(
            "freq_729_sp_RSB",
            NumberValue(default=80*MHz+2*self.parameter_manager.get_param("qubit/vib_freq"), min=20*MHz, max=250*MHz, unit="MHz", precision=8),
            tooltip="729 double pass frequency",
            group='SDF'
        )
        self.setattr_argument(
            "amp_729_sp_BSB",
            NumberValue(default=self.parameter_manager.get_param("SDF/mode_single_ion/amp_729_sp"), min=0, max=0.8, precision=8),
            tooltip="729 single pass attenuation",
            group='SDF'
        )
        self.setattr_argument(
            "amp_729_sp_RSB",
            NumberValue(default=self.parameter_manager.get_param("SDF/mode_single_ion/amp_729_sp_aux"), min=0, max=0.8, precision=8),
            tooltip="729 single pass attenuation",
            group='SDF'
        )

        self.setattr_argument(
            "freq_729_dp",
            NumberValue(default=self.parameter_manager.get_param("qubit/Sm1_2_Dm5_2"), min=200*MHz, max=250*MHz, unit="MHz", precision=8),
            tooltip="729 double pass frequency"
        )

        self.setattr_argument(
            "att_729_dp",
            NumberValue(default=self.parameter_manager.get_param("attenuation/729_dp"), min=10*dB, max=30*dB, unit="dB", precision=8),
            tooltip="729 double pass attenuation"
        )
        #time steps
        self.setattr_argument(
            "scan_rabi_t",
            Scannable(
                default=RangeScan(
                    start=0*us,
                    stop=100*us,
                    npoints=30
                ),
                global_min=0*us,
                global_max=10000*us,
                global_step=10*us,
                unit="us"
            ),
            tooltip="Scan parameter for sweeping the 729 double pass on time."
        )

        #sample
        self.setattr_argument(
            "samples_per_time",
            NumberValue(default=100, precision=0, step=1),
            tooltip="Number of samples to take for each time",
        )
        self.setattr_argument("enable_collision_detection", BooleanValue(True))
        self.setattr_argument("enable_thresholding", BooleanValue(True))
        self.setattr_argument(
            "threshold_pmt_count",
            NumberValue(default=self.parameter_manager.get_param("readout/threshold"), precision=8),
            tooltip="Threshold PMT counts",
        )    

    def prepare(self):
        # Create datasets
        num_samples = len(self.scan_rabi_t.sequence)
        self.experiment_data.set_nd_dataset("pmt_counts", [num_samples, self.samples_per_time], broadcast=True)
        self.experiment_data.set_list_dataset("pmt_counts_avg_thresholded", num_samples, broadcast=True)
        self.experiment_data.set_list_dataset("rabi_t", num_samples, broadcast=True)
        #self.experiment_data.set_list_dataset('fit_signal', num_samples, broadcast=True)

        # Enable live plotting
        self.experiment_data.enable_experiment_monitor(
            "pmt_counts_avg_thresholded",
            x_data_name="rabi_t",
            pen=False
            #fit_data_name='fit_signal'
        )

        s_f=stark_shift(self.parameter_manager, 
                        self.parameter_manager.get_param("qubit/Sm1_2_Dm5_2"), 
                        self.rot_x_freq_729_sp,
                        1.0/self.rot_time/4.0)
        print(s_f/1000, " kHz")
        #print(1.0/self.rot_time/4.0)
        self.rot_x_freq_729_sp-=s_f

    @rpc
    def send_exp_para(
        self
    ):
        send_exp_para(["VAET", {

                "freq_sp_rot": self.rot_x_freq_729_sp,
                "amp_sp_rot": self.rot_x_amp_729_sp,
                "freq_sp_BSB": self.freq_729_sp_BSB, 
                "freq_sp_RSB": self.freq_729_sp_RSB,
                "amp_sp_BSB":  self.amp_729_sp_BSB,  
                "amp_sp_RSB": self.amp_729_sp_RSB,

                "freq_sp":self.J_freq_729_sp,
                "amp_sigma_x":self.Jx_amp_729_sp,
                "amp_sigma_y":self.Jy_amp_729_sp,
                "num_loop":max(self.samples_per_time+100,200)
            }]) 

            
    # @rpc
    # def send_exp_para(self):
    #     send_exp_para(["SingleTone",{"freq": self.rot_x_freq_729_sp,"amp": self.rot_x_amp_729_sp, "num_loop":max(self.samples_per_time+100,300)}])

    @kernel
    def run(self):

        self.setup_run()
        self.seq.ion_store.run()
        delay(50*us)

        time_i = 0
        while time_i < len(self.scan_rabi_t.sequence):

            rabi_time=self.scan_rabi_t.sequence[time_i]

            #PMT
            total_thresh_count = 0
            sample_num=0

            # Cool
            self.seq.ion_store.run()
            self.send_exp_para()

            # Collision Detection
            is_ion_good = True
            num_try_save_ion = 0 
            delay(50*ms)


            while sample_num<self.samples_per_time:

                if is_ion_good:
                
                    #line trigger
                    if self.seq.ac_trigger.run(self.core, self.core.seconds_to_mu(25*ms), self.core.seconds_to_mu(50*us) ) <0 : 
                        continue
                   
                    #854 repump
                    self.seq.repump_854.run()
                    #  Cool
                    self.seq.doppler_cool.run()
                    self.seq.sideband_cool.run()

                    # rabi 
                    self.ttl_rf_switch_AWG_729SP.on()
                    self.ttl_rf_switch_DDS_729SP.off()

                    self.dds_729_dp.set(self.freq_729_dp)
                    self.dds_729_dp.set_att(self.att_729_dp)

                    self.dds_729_sp.sw.off()
                    self.dds_729_sp_aux.sw.off()
                    delay(2*us)
                    
                    
                    # rotation x -pi/2
                    self.ttl_awg_trigger.pulse(1*us)
                    delay(2*us)
                    self.dds_729_dp.sw.on()
                    delay(self.rot_time)
                    self.dds_729_dp.sw.off()
                    delay(2*us)

                    # Hamiltonian
                    self.ttl_awg_trigger.pulse(1*us)
                    delay(2*us)
                    self.dds_729_dp.sw.on()
                    delay(rabi_time)
                    self.dds_729_dp.sw.off()
                    delay(2*us)
                    
                    # rotation x pi/2
                    self.ttl_awg_trigger.pulse(1*us)
                    delay(2*us)
                    self.dds_729_dp.sw.on()
                    delay(self.rot_time)
                    self.dds_729_dp.sw.off()
                    delay(2*us)

                    #turn off the awg
                    self.ttl_awg_trigger.pulse(1*us)


                    self.ttl_rf_switch_AWG_729SP.off()
                    self.ttl_rf_switch_DDS_729SP.on()

                    #qubit readout
                    num_pmt_pulses=self.seq.readout_397.run()

                    if num_pmt_pulses < self.threshold_pmt_count and self.enable_collision_detection:

                        # collision detection
                        self.seq.repump_854.run()
                        self.seq.doppler_cool.run()
                        num_pmt_pulses_detect=self.seq.readout_397.run()
                        self.seq.ion_store.run()
                        delay(20*us)

                        if num_pmt_pulses_detect < self.threshold_pmt_count:
                            is_ion_good = False
                            
                    if is_ion_good:
                        sample_num+=1
                        # Update dataset
                        self.experiment_data.insert_nd_dataset("pmt_counts",
                                                    [time_i, sample_num],
                                                    num_pmt_pulses)
                        
                        if num_pmt_pulses < self.threshold_pmt_count:
                            total_thresh_count += 1

                        delay(2*ms)
                else:
                    self.seq.ion_store.run()
                    delay(0.2*s)
                    self.seq.doppler_cool.run()
                    num_pmt_pulses_detect=self.seq.readout_397.run()
                    if num_pmt_pulses_detect >= self.threshold_pmt_count:
                        is_ion_good = True
                        num_try_save_ion = 0
                    else:
                        num_try_save_ion += 1
                    
                    if(num_try_save_ion>60):
                        print("Ion Lost!!!")
                        time_i=+100000
                        sample_num+=10000
                        break
                     
            
            self.experiment_data.append_list_dataset("rabi_t", rabi_time / us)
            self.experiment_data.append_list_dataset("pmt_counts_avg_thresholded",
                                          float(total_thresh_count) / self.samples_per_time)
            time_i += 1
            
            delay(5*ms)

        self.seq.ion_store.run()



    