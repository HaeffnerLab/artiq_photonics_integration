from acf.experiment import _ACFExperiment
from acf_sequences.sequences import sequences
from acf_config.arguments_definition import argument_manager
from acf.utils import get_config_dir
from artiq.experiment import *

from acf.function.fitting import *

from scipy.interpolate import interp1d
from awg_utils.transmitter import send_exp_para

class att729_scan(_ACFExperiment):

    def build(self): 
        
        self.setup(sequences)

        #setup sequences
        self.seq.doppler_cool.add_arguments_to_gui()
        self.seq.sideband_Radial.add_arguments_to_gui()
        self.seq.repump_854.add_arguments_to_gui()
        self.seq.readout_397.add_arguments_to_gui()
        self.seq.ion_store.add_arguments_to_gui()


        self.seq.cam_two_ions.build()
        
        self.setattr_argument(
            "rabi_t",
            NumberValue(default=2000*us, min=0*us, max=5*ms, unit="us",precision=8),
            group="rabi"
        )
        self.setattr_argument("vib_mode", EnumerationValue(["Radial_mode1","Radial_mode2"], default="Radial_mode1"))
        self.setattr_argument(
            "freq_729_dp",
            NumberValue(default=self.parameter_manager.get_param("qubit/Sm1_2_Dm5_2"), min=200*MHz, max=250*MHz, unit="MHz", precision=8),
            tooltip="729 double pass frequency",
            group="rabi"
        )
        self.setattr_argument(
            "att_729_dp",
            NumberValue(default=10*dB, min=8*dB, max=31*dB, unit="dB", precision=8),
            tooltip="729 double pass attenuation",
            group="rabi"
        )
        self.setattr_argument(
            "freq_729_sp",
            NumberValue(default=self.parameter_manager.get_param("frequency/729_sp"), min=40*MHz, max=160*MHz, unit="MHz", precision=8),
            tooltip="729 double pass frequency",
            group="rabi"
        )
        self.setattr_argument(
            "att_729_sp",
            NumberValue(default=13*dB, min=8, max=31, unit='dB', precision=8),
            tooltip="729 double pass attenuation",
            group="rabi"
        )

        self.setattr_argument(
            "scan_att_729",
            Scannable(
                default=RangeScan(
                    start=9*dB,
                    stop=30*dB,
                    npoints=20
                ),
                global_min=8*dB,
                global_max=31.5*dB,
                unit="dB",
                precision=6
            ),
            tooltip="Scan parameters for sweeping the 397 laser."
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
        self.setattr_argument("cooling_option", EnumerationValue(["opticalpumping", "sidebandcool_Radial"], default="sidebandcool_Radial"))
        


    def get_qubit_freq(self)->float:
        return self.get_dataset('__param__qubit/Sm1_2_Dm5_2', archive=False)
    def get_Radial_vib_freq1(self)->float:
        return self.get_dataset('__param__sideband_Radial/vib_freq0_1', archive=False)
    def get_Radial_vib_freq2(self)->float:
        return self.get_dataset('__param__sideband_Radial/vib_freq0_2', archive=False)
    
    def prepare(self):
        # Create datasets
        num_samples = len(self.scan_att_729.sequence)
        self.experiment_data.set_nd_dataset("pmt_counts", [num_samples, self.samples_per_time], broadcast=True)
        self.experiment_data.set_list_dataset("pos", num_samples, broadcast=True)
        self.experiment_data.set_list_dataset("pmt_counts_avg", num_samples, broadcast=True)
        self.experiment_data.set_list_dataset("attenuation_dB", num_samples, broadcast=True)

        # Enable live plotting
        self.experiment_data.enable_experiment_monitor(
            "pmt_counts_avg",
            x_data_name="attenuation_dB",
            pen=False,
            pos_data_name="pos"
        )

        
    @kernel
    def rabi_AWG(self, pulse_time, freq_729_dp, att_729_dp):
        
        #double pass 
        self.dds_729_radial_dp.set(freq_729_dp)
        self.dds_729_radial_dp.set_att(att_729_dp)
        self.dds_729_radial_sp.set(self.freq_729_sp)
        self.dds_729_radial_sp.set_att(self.att_729_sp)

        #turn on the dds
        self.dds_729_radial_sp.cfg_sw(True)
        delay(10*us)
        self.dds_729_radial_dp.sw.on()
        delay(pulse_time)
        self.dds_729_radial_dp.sw.off()
        self.dds_729_radial_sp.cfg_sw(False)
        delay(5*us)
        

    @kernel
    def exp_seq(self, freq_729_dp_vib, SBC_att_729_dp, ion_status_detect):
        #854 repump
        self.seq.repump_854.run()
        
        #  Cool
        self.seq.doppler_cool.run()

        freq_diff_dp= self.freq_diff_dp if ion_status_detect==2 else 0.0 

        if self.cooling_option=="sidebandcool_Radial":
            self.seq.sideband_Radial.run(
                att_729_here=SBC_att_729_dp,
                freq_diff_dp=freq_diff_dp
            )
        else:
            self.seq.op_pump.run(freq_diff_dp=freq_diff_dp) 
            
        # rabi 
        self.rabi_AWG(self.rabi_t, freq_729_dp_vib+freq_diff_dp, self.att_729_dp)

        
    @kernel
    def run(self):

        print("Running the script")
        self.setup_run()
        self.seq.ion_store.run()
        delay(50*us)

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
            i=10000000
            print("Maybe two bright ions????????????????????????????????????????????????????????????????")
        ion_status_detect = ion_status_detect_last



        if self.vib_mode=="Radial_mode1":
            freq_729_dp_vib=self.freq_729_dp+self.get_Radial_vib_freq1()/2.0
        else: #if self.vib_mode=="Radial_mode2":
            freq_729_dp_vib=self.freq_729_dp+self.get_Radial_vib_freq2()/2.0

        print(self.freq_729_dp-self.get_Radial_vib_freq1()/2.0)
        print(self.freq_729_dp-self.get_Radial_vib_freq2()/2.0)
        print(self.rabi_t)
        print(self.att_729_dp, self.att_729_sp)
        self.core.break_realtime()


        i=0
        while i < len(self.scan_att_729.sequence):

            total_thresh_count = 0
            sample_num=0
            SBC_att_729_dp =self.scan_att_729.sequence[i]
            num_try_save_ion = 0 
            delay(20*us)

            while sample_num<self.samples_per_time:
                if ion_status_detect==1 or ion_status_detect==2:
                    #line trigger
                    if self.seq.ac_trigger.run(self.core, self.core.seconds_to_mu(25*ms), self.core.seconds_to_mu(50*us) ) <0 : 
                        continue
                    
                    delay(50*us)

                    self.exp_seq(freq_729_dp_vib, SBC_att_729_dp, ion_status_detect)
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


            self.experiment_data.append_list_dataset("attenuation_dB", SBC_att_729_dp/dB)
            self.experiment_data.append_list_dataset("pos", ion_status_detect)
            self.experiment_data.append_list_dataset("pmt_counts_avg",
                                        float(total_thresh_count) / self.samples_per_time)
            
            i=i+1
            self.core.break_realtime()

        self.seq.ion_store.run()
        delay(5*us)

