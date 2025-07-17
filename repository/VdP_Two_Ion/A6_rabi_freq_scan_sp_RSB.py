from acf.experiment import _ACFExperiment
from acf_sequences.sequences import sequences
from acf_config.arguments_definition import argument_manager
from acf.utils import get_config_dir
from artiq.experiment import *

from acf.function.fitting import *

from scipy.interpolate import interp1d
from awg_utils.transmitter import send_exp_para

class A6_Rabi_Freq_AWG_Sp_RSB(_ACFExperiment):

    def build(self): 
        
        self.setup(sequences)

        #setup sequences
        self.seq.doppler_cool.add_arguments_to_gui()
        self.seq.sideband_cool_2mode.add_arguments_to_gui()
        self.seq.repump_854.add_arguments_to_gui()
        self.seq.readout_397.add_arguments_to_gui()
        self.seq.ion_store.add_arguments_to_gui()

        self.setup_fit(fitting_func ,'Lorentzian', -999)

        self.seq.cam_two_ions.build()
        
        self.setattr_argument(
            "rabi_t",
            NumberValue(default=100*us, min=0*us, max=5*ms, unit="us",precision=8),
            group="rabi"
        )
        self.setattr_argument(
            "att_729_dp",
            NumberValue(default=30*dB, min=8*dB, max=31*dB, unit="dB", precision=8),
            tooltip="729 double pass attenuation",
            group="rabi"
        )
        self.setattr_argument(
            "freq_729_dp",
            NumberValue(default=self.parameter_manager.get_param("qubit/Sm1_2_Dm5_2"), min=40*MHz, max=260*MHz, unit="MHz", precision=8),
            tooltip="729 double pass frequency",
            group="rabi"
        )


        self.setattr_argument(
            "amp_729_sp",
            NumberValue(default=0.05, min=0, max=1, precision=8),
            tooltip="729 double pass attenuation",
            group="scan_freq_sp"
        )

        self.setattr_argument(
            "scan_freq_729_sp",
            Scannable(
                default=RangeScan(
                    start=self.parameter_manager.get_param("frequency/729_sp")-0.003*MHz,
                    stop=self.parameter_manager.get_param("frequency/729_sp")+0.003*MHz,
                    npoints=40
                ),
                global_min=50*MHz,
                global_max=250*MHz,
                global_step=1*kHz,
                unit="MHz",
                precision=8
            ),
            tooltip="Scan parameter for sweeping the 729 double pass laser.",
            group="scan_freq_sp"
        )

        self.setattr_argument(
            "freq_729_sp_fixed",
            NumberValue(default=self.parameter_manager.get_param("frequency/729_sp"), min=40*MHz, max=260*MHz, unit="MHz", precision=8),
            tooltip="729 double pass frequency",
            group="scan_freq_sp"
        )
        self.setattr_argument(
            "amp_729_sp_fixed",
            NumberValue(default=0.05, min=0, max=1, precision=8),
            tooltip="729 double pass attenuation",
            group="scan_freq_sp"
        )

        self.setattr_argument(
            "samples_per_time",
            NumberValue(default=50, precision=0, step=1),
            tooltip="Number of samples to take for each time",
        )
        self.setattr_argument(
            "freq_diff_dp",
            NumberValue(default=self.parameter_manager.get_param("VdP2mode/freq_diff_dp"), min=-56*MHz, max=250*MHz, unit="MHz", precision=8),
            tooltip="double pass frequency different in two position"
        )
        self.setattr_argument("cooling_option", EnumerationValue(["sidebandcool_mode1","sidebandcool_mode2", "sidebandcool2mode", "opticalpumping", "sidebandcool_single_ion"], default="sidebandcool2mode"))

        self.setattr_argument(
                "Ca_line", 
                EnumerationValue([
                                  "RSB_mode1", 
                                  "RSB_mode2", 
                                  "nothing"]
                                 , default="RSB_mode1")
            )
        
        self.freq_vib1=self.get_vib_freq1()
        self.freq_vib2=self.get_vib_freq2()
        self.sideband_mode1_att729=self.parameter_manager.get_float_param('sideband2mode/mode1_att_729')
        self.sideband_mode1_att854=self.parameter_manager.get_float_param('sideband2mode/mode1_att_854')
        self.sideband_mode2_att729=self.parameter_manager.get_float_param('sideband2mode/mode2_att_729')
        self.sideband_mode2_att854=self.parameter_manager.get_float_param('sideband2mode/mode2_att_854')

    def get_qubit_freq(self)->float:
        return self.get_dataset('__param__qubit/Sm1_2_Dm5_2', archive=False)
    def get_vib_freq1(self)->float:
        return self.get_dataset('__param__VdP2mode/vib_freq1', archive=False)
    def get_vib_freq2(self)->float:
        return self.get_dataset('__param__VdP2mode/vib_freq2', archive=False)
    
    def prepare(self):
        self.fitting_func.setup(len(self.scan_freq_729_sp.sequence))
        # Create datasets
        num_samples = len(self.scan_freq_729_sp.sequence)
        self.experiment_data.set_nd_dataset("pmt_counts", [num_samples, self.samples_per_time])
        self.experiment_data.set_list_dataset("pos", num_samples, broadcast=True)
        self.experiment_data.set_list_dataset("pmt_counts_avg", num_samples, broadcast=True)
        self.experiment_data.set_list_dataset("frequencies_MHz", num_samples, broadcast=True)

        # Enable live plotting
        self.experiment_data.enable_experiment_monitor(
            "pmt_counts_avg",
            x_data_name="frequencies_MHz",
            pen=False,
            fit_data_name='fit_signal',
            pos_data_name="pos"

        )



    @kernel
    def rabi_AWG(self,freq_729_dp):
        

        #double pass 
        self.dds_729_dp.set(freq_729_dp)
        self.dds_729_dp.set_att(self.att_729_dp)
        self.ttl_rf_switch_AWG_729SP.on()
        self.dds_729_sp.sw.off()
        self.dds_729_sp_aux.sw.off()

        self.ttl_awg_trigger.pulse(1*us)
        delay(5*us)
        self.dds_729_dp.sw.on()
        delay(self.rabi_t)
        self.dds_729_dp.sw.off()
        delay(5*us)
        self.ttl_awg_trigger.pulse(1*us)

        
        self.ttl_rf_switch_AWG_729SP.off()
        self.ttl_rf_switch_DDS_729SP.on()
        

    @kernel
    def exp_seq(self, ion_status_detect):
        #854 repump
        self.seq.repump_854.run()
        
        #  Cool
        self.seq.doppler_cool.run()
        freq_diff_dp = self.freq_diff_dp if ion_status_detect==2 else 0.0
        if self.cooling_option == "sidebandcool_single_ion":
            self.seq.sideband_cool.run(freq_diff_dp=freq_diff_dp)
        elif self.cooling_option == "sidebandcool_mode2":
            self.seq.sideband_cool.run(freq_offset=self.freq_vib2, 
                                           att_729_here=self.sideband_mode2_att729,
                                           freq_diff_dp=freq_diff_dp, 
                                           att_854_here=self.sideband_mode2_att854) 
        elif self.cooling_option == "sidebandcool_mode1":
          
            self.seq.sideband_cool.run(freq_offset=self.freq_vib1, 
                                           att_729_here=self.sideband_mode1_att729,
                                           freq_diff_dp=freq_diff_dp, 
                                           att_854_here=self.sideband_mode1_att854) 
            
            
        elif self.cooling_option == "sidebandcool2mode":
            self.seq.sideband_cool_2mode.run(freq_diff_dp=freq_diff_dp) 
        else:
            self.seq.op_pump.run(freq_diff_dp=freq_diff_dp) 
        delay(5*us)
        
        # rabi 
        self.rabi_AWG(self.freq_729_dp+freq_diff_dp)
        
    @rpc(flags={'async'})
    def send_exp_para(
        self,
        freq_sp,
        amp_sp
    ):
        send_exp_para(["SDF", {
                "freq_sp_RSB":   self.freq_729_sp_fixed,
                "freq_sp_BSB":   freq_sp,
                "amp_sp_RSB":  self.amp_729_sp_fixed,
                "amp_sp_BSB":   amp_sp,
                "num_loop": 500
            }])  
        
    @kernel
    def run(self):

        print("Running the script")
        self.setup_run()
        self.seq.ion_store.run()
        self.rf.set_voltage(1)
        self.core.break_realtime()

        self.seq.cam_two_ions.cam_setup()

        # Position Detection 1: left up; 2 right dn; 3:both bright; 0:both dark
        ion_status_detect_last=0 #used for detecting if there is a switching event during experiment (record valide last experiment)
        ion_status=1
        ion_status_detect=1

        #detecting the initial position of the ion 
        while ion_status_detect_last!=1 and ion_status_detect_last!=2:
            delay(2*ms)
            self.seq.repump_854.run()
            self.seq.doppler_cool.run()
            delay(5*us)
            ion_status_detect_last=self.seq.cam_two_ions.cam_readout()
            self.seq.ion_store.run()
            delay(1*ms)
        
        if(ion_status_detect_last==3): 
            i=len(self.scan_freq_729_sp.sequence)
            print("Maybe two bright ions????????????????????????????????????????????????????????????????")
        ion_status_detect = ion_status_detect_last

        i=0
        while i < len(self.scan_freq_729_sp.sequence):

            total_thresh_count = 0
            sample_num=0
            rabi_t=self.rabi_t
            freq_729_sp =self.scan_freq_729_sp.sequence[i]


            delay(20*us)
            self.seq.ion_store.run()
            self.core.break_realtime()
           
            num_try_save_ion = 0 

            self.send_exp_para(freq_729_sp , self.amp_729_sp)   
            if self.seq.awg_trigger.run(self.core, self.core.seconds_to_mu(25*ms), self.core.seconds_to_mu(50*us) ) <0 : 
                print("BAD AWG!!!!")
                continue

            while sample_num<self.samples_per_time:
                if ion_status_detect==1 or ion_status_detect==2:
                    #line trigger
                    if self.seq.ac_trigger.run(self.core, self.core.seconds_to_mu(25*ms), self.core.seconds_to_mu(50*us) ) <0 : 
                        continue
                    
                    delay(50*us)

                    self.exp_seq(ion_status_detect)
                    ################################################################################
                    ion_status=self.seq.cam_two_ions.cam_readout()
                    self.seq.ion_store.run()
                    delay(50*us)
                    ################################################################################
                    if ion_status==0: #if the ion is not bright then it's possible it's being kicked
                        # collision detection
                        self.seq.repump_854.run()
                        self.seq.doppler_cool.run()
                        ion_status_detect=self.seq.cam_two_ions.cam_readout() #by the way get the position
                        self.seq.ion_store.run()
                        delay(20*us)
                    else: 
                        ion_status_detect=ion_status

                      
                    if (ion_status_detect==ion_status_detect_last): #ion shouldn't move
                        sample_num+=1
                        # Update dataset
                        # self.experiment_data.insert_nd_dataset("pmt_counts",
                        #                             [i, sample_num],
                        #                             cam_input[0])
                        
                        if ion_status==0:
                            total_thresh_count += 1

                        #total_pmt_counts += cam_input[0]

                        delay(20*us)
                    elif (ion_status_detect==1 or ion_status_detect==2):
                        ion_status_detect_last=ion_status_detect
                        self.seq.ion_store.run()
                        delay(1*s)
                        self.seq.doppler_cool.run()
                        self.seq.ion_store.run()
                    
                    # print(ion_status_detect)
                    # delay(10*ms)

                else:
                    self.seq.ion_store.run()
                    delay(1*s)
                    self.seq.doppler_cool.run()
                    ion_status_detect=self.seq.cam_two_ions.cam_readout()
                    self.seq.ion_store.run()

                    if ion_status_detect==1 or ion_status_detect==2:
                        num_try_save_ion = 0
                        ion_status_detect_last=ion_status_detect
                    else:
                        num_try_save_ion += 1
                    
                    if(num_try_save_ion>60):
                        print("Ion Lost!!!")
                        i=1000000
                        sample_num+=10000
                        break
                    delay(1*ms)


            self.experiment_data.append_list_dataset("frequencies_MHz", freq_729_sp/MHz)
            self.experiment_data.append_list_dataset("pos", ion_status_detect)
            self.experiment_data.append_list_dataset("pmt_counts_avg",
                                        float(total_thresh_count) / self.samples_per_time)
            
            i=i+1
            self.core.break_realtime()

        self.seq.ion_store.run()
        self.rf.set_voltage(0)
        self.core.break_realtime()

        delay(5*us)

    def analyze(self):
        freq=self.get_dataset("frequencies_MHz")
        PMT_count=self.get_dataset('pmt_counts_avg')

        peak=self.fitting_func.fit(freq, PMT_count)[1]


        with self.interactive("Ca+ sideband") as inter:
            inter.setattr_argument(
                "Ca_line", 
                EnumerationValue(["RSB_mode2","RSB_mode1", "nothing"]
                                 , default=self.Ca_line)
            )
        
        freq_sp=self.get_dataset("__param__frequency/729_sp")

        if inter.Ca_line == "RSB_mode1":

            self.parameter_manager.set_param(
                "VdP2mode/freq_RSB_mode1",
                peak*1e6-freq_sp,
                "MHz"
            )
        elif inter.Ca_line == "RSB_mode2":

            self.parameter_manager.set_param(
                "VdP2mode/freq_RSB_mode2",
                peak*1e6-freq_sp,
                "MHz"
            )