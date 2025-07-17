from acf.experiment import _ACFExperiment
from acf_sequences.sequences import sequences
from acf_config.arguments_definition import argument_manager

from artiq.experiment import *
from acf.function.fitting import *
from awg_utils.transmitter import send_exp_para
import time 

class A6_Radial_Ramsey_Scan(_ACFExperiment):

    def build(self):
    
        self.setup(sequences)

        self.seq.sideband_Radial.add_arguments_to_gui()
        self.seq.doppler_cool.add_arguments_to_gui()
        self.seq.repump_854.add_arguments_to_gui()
        self.seq.readout_397.add_arguments_to_gui()
        self.seq.ion_store.add_arguments_to_gui()

        self.seq.cam_two_ions.build()

        ##########################################################################################################################################
	
        self.setattr_argument(
            "freq_729_dp",
            NumberValue(default=self.parameter_manager.get_param("qubit/Sm1_2_Dm5_2"), min=200*MHz, max=250*MHz, unit="MHz", precision=8),
            tooltip="729 double pass frequency",
            group="rabi"
        )
        self.setattr_argument(
            "att_729_dp",
            NumberValue(default=20.0*dB, min=8*dB, max=31*dB, unit="dB", precision=8),
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
            NumberValue(default=self.parameter_manager.get_param("attenuation/729_radial_sp"), min=5*dB, max=31*dB, unit="dB", precision=8),
            tooltip="729 double pass attenuation",
            group="rabi"
        )

        ##########################################################################################################################################
        self.setattr_argument("Motional_Ramsey", BooleanValue(False),group = "Motional Ramsey")

        self.setattr_argument("vib_mode", EnumerationValue(["Radial_mode1","Radial_mode2"], default="Radial_mode1"),group = "Motional Ramsey")



        self.setattr_argument(
            "SB_att_729_dp",
            NumberValue(default=10.0*dB, min=5*dB, max=31*dB, unit="dB", precision=8),
            tooltip="729 double pass attenuation",
            group="Motional Ramsey"
        )
        self.setattr_argument(
            "SB_drive_time",
            NumberValue(default=self.parameter_manager.get_param("pi_time/Radial/RSB_pi_time"), min=0.*us, max=10000*us, unit='us'),
            tooltip="Drive time for the red side band",
            group = "Motional Ramsey"
        )


        self.setattr_argument(
            "Ramsey_wait_time_single",
            NumberValue(default=0.1*us, min=0.*us, max=100000*us, unit='us'),
            tooltip="Ramsey wait time if don't scan this dimension",
            group='Ramsey non-scan setting'
        )
        self.setattr_argument(
            "Ramsey_pulse_time_single",
            NumberValue(default=self.parameter_manager.get_param("pi_time/Radial/pi_time")/2.0, min=0.*us, max=100*us, unit='us'),
            tooltip="Ramsey pulse time if don't scan this dimension",
            group='Ramsey non-scan setting'
        )   
        self.setattr_argument(
            "Ramsey_phase_single",
            NumberValue(default=0, min=0, max=1),
            tooltip="Scan parameter for Ramsey pulse phase difference (in turns) if don't scan this dimension",
            group='Ramsey non-scan setting'
        )


        self.setattr_argument(
            "Ramsey_wait_time",
            Scannable(
                default=RangeScan(
                    start=0.*us,
                    stop=10000*us,
                    npoints=100
                ),
                global_min=0*us,
                global_max=100000*us,
                global_step=10*us,
                unit="us"
            ),
            tooltip="Scan parameter for Ramsey wait time.",
            group='Ramsey scan setting'
        )   
        self.setattr_argument(
            "Ramsey_pulse_time",
            Scannable(
                default=RangeScan(
                    start=0.*us,
                    stop=10*us,
                    npoints=100
                ),
                global_min=0*us,
                global_max=100*us,
                global_step=10*us,
                unit="us"
            ),
            tooltip="Scan parameter for Ramsey pulse time.",
            group='Ramsey scan setting'
        )
        self.setattr_argument(
            "Ramsey_phase",
            Scannable(
                default=RangeScan(
                    start=0,
                    stop=1,
                    npoints=20
                )
            ),
            tooltip="Scan parameter for Ramsey pulse phase difference (in turns)",
            group='Ramsey scan setting'
        )

        self.setattr_argument(
            "samples_per_scan",
            NumberValue(default=50, precision=0, step=1),
            tooltip="Number of samples to take for each scan configuration",
        )

        self.setattr_argument("Scan_Type", EnumerationValue(["Ramsey_wait_time", "Ramsey_pulse_time", "Ramsey_phase"], default="Ramsey_phase"))
   
        self.setattr_argument("cooling_option", EnumerationValue(["opticalpumping", "sidebandcool_Radial"], default="sidebandcool_Radial"))

        self.scan_name='Ramsey_wait_time_(us)'
        ###################################################################################################################################################################################
        
        self.sideband_mode1_att729=self.parameter_manager.get_float_param('sideband2mode/mode1_att_729')
        self.sideband_mode1_att854=self.parameter_manager.get_float_param('sideband2mode/mode1_att_854')
        self.sideband_mode2_att729=self.parameter_manager.get_float_param('sideband2mode/mode2_att_729')
        self.sideband_mode2_att854=self.parameter_manager.get_float_param('sideband2mode/mode2_att_854')
        self.freq_sp_SB=self.parameter_manager.get_param("frequency/729_sp")-2*self.parameter_manager.get_param("qubit/vib_freq")

        if self.vib_mode=="Radial_mode1":
            self.freq_radial_vib=self.get_dataset("__param__sideband_Radial/vib_freq0_1")
        elif self.vib_mode=="Radial_mode2":
            self.freq_radial_vib=self.get_dataset("__param__sideband_Radial/vib_freq0_2")

    def get_qubit_freq(self)->float:
        return self.get_dataset('__param__qubit/Sm1_2_Dm5_2', archive=False)
    def get_vib_freq1(self)->float:
        return self.get_dataset('__param__VdP2mode/vib_freq1', archive=False)
    def get_vib_freq2(self)->float:
        return self.get_dataset('__param__VdP2mode/vib_freq2', archive=False)
    

    def prepare(self):
        scan_length=max(len(self.Ramsey_wait_time.sequence), max(len(self.Ramsey_pulse_time.sequence),len(self.Ramsey_phase.sequence)))
        self.scan_param0 =[0.0 *us for i in range(scan_length)] 
        self.scan_param1 =[0.0 *us for i in range(scan_length)]
        self.scan_param2 =[0.0 for i in range(scan_length)]        
        self.scan_axis=[0.0 for i in range(scan_length)]   
        self.num_scan_samples = 0

        if self.Scan_Type == "Ramsey_wait_time":
            for i in range(len(self.Ramsey_wait_time.sequence)):
                self.scan_param0[i]=self.Ramsey_wait_time.sequence[i]
                self.scan_param1[i]=self.Ramsey_pulse_time_single
                self.scan_param2[i]=self.Ramsey_phase_single

                self.scan_axis[i]=self.Ramsey_wait_time.sequence[i]/us
            self.num_scan_samples=len(self.Ramsey_wait_time.sequence)
            self.scan_name='Ramsey_wait_time_(us)'


        elif self.Scan_Type == "Ramsey_pulse_time":
            for i in range(len(self.Ramsey_pulse_time.sequence)):
                self.scan_param0[i]=self.Ramsey_wait_time_single
                self.scan_param1[i]=self.Ramsey_pulse_time.sequence[i]
                self.scan_param2[i]=self.Ramsey_phase_single

                self.scan_axis[i]=self.Ramsey_pulse_time.sequence[i]/us
            self.num_scan_samples=len(self.Ramsey_pulse_time.sequence)
            self.scan_name='Ramsey_pulse_time_(us)'   
        else: #"Ramsey_phase"
            for i in range(len(self.Ramsey_phase.sequence)):
                self.scan_param0[i]=self.Ramsey_wait_time_single
                self.scan_param1[i]=self.Ramsey_pulse_time_single
                self.scan_param2[i]=self.Ramsey_phase.sequence[i]

                self.scan_axis[i]=self.Ramsey_phase.sequence[i]
            self.num_scan_samples=len(self.Ramsey_phase.sequence)
            self.scan_name='Ramsey_phase_(turns)'


        # create datasets
        self.experiment_data.set_nd_dataset("pmt_counts", [scan_length, self.samples_per_scan])
        
        # Dataset mainly for plotting
        self.experiment_data.set_list_dataset("pmt_counts_avg", scan_length, broadcast=True)
        self.experiment_data.set_list_dataset(self.scan_name, scan_length, broadcast=True)


        self.experiment_data.set_list_dataset("pos", scan_length, broadcast=True)

        # Enable live plotting
        self.experiment_data.enable_experiment_monitor(
            "pmt_counts_avg",
            x_data_name=self.scan_name,
            pen=True,
            pos_data_name="pos"
        )

        if self.vib_mode=="mode1":
            self.freq_sp_SB=self.parameter_manager.get_param("frequency/729_sp")+self.parameter_manager.get_param("VdP2mode/vib_freq1")
        elif self.vib_mode=="mode2":
            self.freq_sp_SB=self.parameter_manager.get_param("frequency/729_sp")+self.parameter_manager.get_param("VdP2mode/vib_freq2")
        else:
            self.freq_sp_SB=self.parameter_manager.get_param("frequency/729_sp")+2*self.parameter_manager.get_param("qubit/vib_freq")
            print(self.freq_sp_SB)


    @kernel
    def Ramsey(self, pulse_time:float, wait_time:float, phase:float)-> None:

        self.dds_729_radial_dp.set(self.freq_729_dp)
        self.dds_729_radial_dp.set_att(self.att_729_dp)
        self.dds_729_radial_sp.set(self.freq_729_sp)
        self.dds_729_radial_sp.set_att(self.att_729_sp)

        # pi/2
        self.dds_729_radial_dp.sw.on()
        self.dds_729_radial_sp.cfg_sw(True)
        delay(pulse_time)
        self.dds_729_radial_dp.sw.off()
        self.dds_729_radial_sp.cfg_sw(False)


        delay(wait_time)

       
        # pi/2
        self.dds_729_radial_dp.set(self.freq_729_dp)
        self.dds_729_radial_sp.set(self.freq_729_sp, phase=phase)
        self.dds_729_radial_dp.sw.on()
        self.dds_729_radial_sp.cfg_sw(True)
        delay(pulse_time)
        self.dds_729_radial_dp.sw.off()
        self.dds_729_radial_sp.cfg_sw(False)

    
    @kernel
    def Ramsey_Motion(self,  pulse_time:float, wait_time:float, phase:float)-> None:

        #double pass
        self.dds_729_radial_dp.set(self.freq_729_dp)
        self.dds_729_radial_dp.set_att(self.att_729_dp)

        #single pass for pi/2 rotation
        self.dds_729_radial_sp.set(self.freq_729_sp)
        self.dds_729_radial_sp.set_att(self.att_729_sp)

        #single pass aux for pi rotation of RSB
        self.dds_729_radial_sp_aux.set_att(self.att_729_sp)
        self.dds_729_radial_sp_aux.set(self.freq_729_sp+self.freq_radial_vib)
        
        self.dds_729_radial_sp.cfg_sw(True)
        self.dds_729_radial_sp_aux.cfg_sw(False)
        self.dds_729_radial_dp.sw.off()
        delay(10*us)


        # pi/2
        self.dds_729_radial_dp.sw.on()
        delay(pulse_time)
        self.dds_729_radial_dp.sw.off()

        #RSB pi pulse
        self.dds_729_radial_dp.set_att(self.SB_att_729_dp)
        self.dds_729_radial_sp_aux.cfg_sw(True)
        self.dds_729_radial_sp.cfg_sw(False)
        delay(5*us)


        self.dds_729_radial_dp.sw.on()
        delay(self.SB_drive_time) 
        self.dds_729_radial_dp.sw.off()

        delay(wait_time)

        # RSB pi pulse
        self.dds_729_radial_dp.sw.on()
        delay(self.SB_drive_time) 
        self.dds_729_radial_dp.sw.off()



        # ######################################################## pi/2 ###################################################
        self.dds_729_radial_sp_aux.cfg_sw(False)
        self.dds_729_radial_sp.cfg_sw(True)
        self.dds_729_radial_dp.set_att(self.att_729_dp)
        self.dds_729_radial_sp.set(self.freq_729_sp, phase=phase)
        delay(5*us)

        self.dds_729_radial_dp.sw.on()
        delay(pulse_time)
        self.dds_729_radial_dp.sw.off()

        # Turn off the SP
        self.dds_729_radial_sp.cfg_sw(False)
        self.dds_729_radial_sp_aux.cfg_sw(False)

    @kernel
    def exp_seq(self, 
                freq_729_dp,
                pulse_time_here, 
                wait_time_here, 
                phase_here, 
                ion_status_detect):
        #854 repump
        self.seq.repump_854.run()
        
        #  Cool
        self.seq.doppler_cool.run()

        # if self.enable_Raman_SBC:
        #    self.seq.sideband_Raman.run()

        freq_diff_dp = 0.0
        
        #self.seq.sideband_Radial.run(freq_diff_dp=freq_diff_dp)

        
        if self.cooling_option == "sidebandcool_Radial":
            self.seq.sideband_Radial.run(freq_diff_dp=freq_diff_dp)
        else:
            self.seq.op_pump.run(freq_diff_dp=freq_diff_dp) 
        delay(5*us)
        
        # rabi 
        if self.Motional_Ramsey:
            self.Ramsey_Motion(pulse_time=pulse_time_here, wait_time=wait_time_here, phase=phase_here)
        else:
            self.Ramsey( pulse_time=pulse_time_here, wait_time=wait_time_here, phase=phase_here)


    @kernel
    def run(self):

        print("Running the script")
        self.setup_run()
        self.seq.ion_store.run()
        self.core.break_realtime()

        self.seq.cam_two_ions.cam_setup()

        # Position Detection 1: left up; 2 right dn; 3:both bright; 0:both dark
        ion_status_detect_last=0 #used for detecting if there is a switching event during experiment (record valide last experiment)
        ion_status=1
        ion_status_detect=1
        num_try_save_ion = 0 

        #detecting the initial position of the ion 
        # while ion_status_detect_last!=1 and ion_status_detect_last!=2:
        #     delay(2*ms)
        #     self.seq.repump_854.run()
        #     self.seq.doppler_cool.run()
        #     delay(5*us)
        #     ion_status_detect_last=self.seq.cam_two_ions.cam_readout()
        #     self.seq.ion_store.run()
        #     delay(1*ms)
        ion_status_detect = ion_status_detect_last

        last_time_calibrate=-5000.

        iter=0
        while iter < self.num_scan_samples:

            total_thresh_count = 0
            num_try_save_ion = 0 
            sample_num=0
            delay(20*us)

            self.seq.ion_store.run()
            

            phase_here=self.scan_param2[iter]
            wait_time_here=self.scan_param0[iter]
            pulse_time_here=self.scan_param1[iter]
            self.core.break_realtime()

            while sample_num<self.samples_per_scan:
               

                if ion_status_detect==1 or ion_status_detect==2:
                    #line trigger
                    if self.seq.ac_trigger.run(self.core, self.core.seconds_to_mu(25*ms), self.core.seconds_to_mu(50*us) ) <0 : 
                        continue
                    
                    delay(50*us)

                    self.exp_seq(self.freq_729_dp,
                                 pulse_time_here, 
                                wait_time_here, 
                                phase_here,
                                ion_status_detect)
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

                      
                    if (ion_status_detect==ion_status_detect_last and ion_status_detect==1):# and (ion_status_detect==1 or ion_status_detect==2) and (ion_status!=3)): #ion shouldn't move
                        sample_num+=1
                        # Update dataset
                        self.experiment_data.insert_nd_dataset("pmt_counts",
                                                    [iter, sample_num],
                                                    ion_status)
                        
                        if ion_status==0:
                            total_thresh_count += 1

                        #total_pmt_counts += cam_input[0]

                        self.core.break_realtime()
                    elif ion_status_detect==ion_status_detect_last and ion_status_detect==2: 
                        self.seq.rf.tickle()

                    elif (ion_status_detect==1 or ion_status_detect==2):
                        ion_status_detect_last=ion_status_detect
                        self.seq.ion_store.run()
                        delay(1*s)
                    

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
                    
                    if(num_try_save_ion>600):
                        print("Ion Lost!!!")
                        i=1000000
                        sample_num+=10000
                        break
                    delay(1*ms)
                    self.core.break_realtime()


            self.experiment_data.append_list_dataset(self.scan_name, self.scan_axis[iter])
            self.experiment_data.append_list_dataset("pos", ion_status_detect)
            self.experiment_data.append_list_dataset("pmt_counts_avg",
                                        float(total_thresh_count) / self.samples_per_scan)
            
            iter=iter+1
            self.core.break_realtime()

        self.seq.ion_store.run()
        self.core.break_realtime()