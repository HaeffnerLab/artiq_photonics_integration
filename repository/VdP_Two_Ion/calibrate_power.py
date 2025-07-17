
from artiq.experiment import *

from acf.experiment import _ACFExperiment
from acf_sequences.sequences import sequences
from acf_config.arguments_definition import argument_manager
from acf.utils import get_config_dir
from scipy.signal import savgol_filter
from scipy.interpolate import interp1d
import numpy as np

class Calibrate_Power(_ACFExperiment):
    def build(self):
        self.setup(sequences)
        self.seq.ion_store.add_arguments_to_gui()

        self.setattr_device("sampler0")            
        
        self.setattr_argument(
            "samples_per_shot",
            NumberValue(default=20, precision=0, step=1),
            tooltip="Number of samples to take for each frequency"
        )

       
        self.setattr_argument(
            "att_729_dp_pi",
            NumberValue(default=self.parameter_manager.get_param("pi_time/att_729_dp"), min=10*dB, max=30*dB, unit="dB", precision=8),
            tooltip="729 double pass amplitude for resonance",
            group='Pi pulse excitation'
        )

        self.setattr_argument(
            "att_729_sp_pi",
            NumberValue(default=self.parameter_manager.get_param("attenuation/729_sp"), min=10*dB, max=30*dB, unit="dB", precision=8),
            tooltip="729 double pass amplitude for resonance",
            group='Pi pulse excitation'
        )
        self.setattr_argument(
            "PI_drive_time",
            NumberValue(default=self.parameter_manager.get_param("pi_time/pi_time"), min=0.*us, max=1000*us, unit='us', precision=8),
            tooltip="Drive time for pi excitation",
            group='Pi pulse excitation'
        )


        
    def prepare(self):
        self.param=[
            "standard",
           "VdP1mode/Rabi_Freq_2RSB",
           "VdP1mode/Rabi_Freq_BSB",
           "VdP2mode/Rabi_Freq_mode1_2RSB",
           "VdP2mode/Rabi_Freq_mode2_2RSB",
           "VdP2mode/Rabi_Freq_mode1_BSB",
           "VdP2mode/Rabi_Freq_mode2_BSB"
        ]
        self.freq_729_dp=[self.parameter_manager.get_param("qubit/Sm1_2_Dm5_2") for _ in range(len(self.param))]

        self.att_729_dp=[
            self.att_729_dp_pi,
            self.parameter_manager.get_param("VdP1mode/att_729_dp"),
            self.parameter_manager.get_param("VdP1mode/att_729_dp"),
            self.parameter_manager.get_param("VdP2mode/att_729_dp"),
            self.parameter_manager.get_param("VdP2mode/att_729_dp"),
            self.parameter_manager.get_param("VdP2mode/att_729_dp"),
            self.parameter_manager.get_param("VdP2mode/att_729_dp")
                         ]
        freq_sp=self.parameter_manager.get_param("frequency/729_sp")

        self.freq_729_sp=[
            freq_sp,
            freq_sp+self.parameter_manager.get_param("VdP1mode/freq_2RSB"),
            freq_sp+self.parameter_manager.get_param("VdP1mode/freq_BSB"),
            freq_sp+self.parameter_manager.get_param("VdP2mode/freq_2RSB_mode1"),
            freq_sp+self.parameter_manager.get_param("VdP2mode/freq_2RSB_mode2"),
            freq_sp+self.parameter_manager.get_param("VdP2mode/freq_BSB_mode1"),
            freq_sp+self.parameter_manager.get_param("VdP2mode/freq_BSB_mode2")
        ]

        self.att_729_sp=[
            self.att_729_sp_pi,
            self.parameter_manager.get_param("VdP1mode/att_2RSB_sp"), 
            self.parameter_manager.get_param("VdP1mode/att_BSB_sp"),
            self.parameter_manager.get_param("VdP2mode/att_729_mode1_2RSB"),
            self.parameter_manager.get_param("VdP2mode/att_729_mode2_2RSB"),
            self.parameter_manager.get_param("VdP2mode/att_729_mode1_BSB"),
            self.parameter_manager.get_param("VdP2mode/att_729_mode2_BSB")
        ]

        self.volt=[0.0]*len(self.freq_729_dp)



    @kernel
    def run(self):

        self.setup_run()
        
        self.sampler0.init()            
        self.core.break_realtime()

        #protect ion
        self.seq.ion_store.run()
        delay(5*us)

        ##################################################################################################################################################
        #self.dds_729_dp.set_att(self.attenuation_729_dp)
        self.dds_729_sp.set_att(self.att_729_sp[0])
        self.dds_729_sp.set(self.freq_729_sp[0])
        self.dds_729_dp.sw.on()
        self.dds_729_sp.sw.on()
        self.core.break_realtime()
        ##################################################################################################################################################

        n_channels = 8                                                                                          
        for i in range(n_channels):                                                     #loops for each sampler channel 
            self.sampler0.set_gain_mu(7-i, 0)                                           #sets each channel's gain to 0db

        ##################################################################################################################################################
        smp = [0.0]*n_channels                                                            #creates list of 8 floating point variables
        self.core.break_realtime()
        delay(3*s)

        for _ in range(self.samples_per_shot):
    
            for i in range(len(self.freq_729_dp)):
                self.dds_729_dp.set(self.freq_729_dp[i])
                self.dds_729_sp.set(self.freq_729_sp[i])
                self.dds_729_sp.set_att(self.att_729_sp[i])
                self.dds_729_dp.set_att(self.att_729_dp[i])

                delay(50*ms) 
                    
                self.sampler0.sample(smp)  
                self.core.break_realtime()                                              
                        
                self.volt[i] += smp[0]
        
        for i in range(0, len(self.freq_729_dp)):
            self.volt[i] /= self.volt[0]
        #protect ion
        self.seq.ion_store.run()
        self.dds_729_dp.sw.off()
        self.dds_729_sp.sw.off()
        self.dds_729_sp_aux.sw.off()


    def analyze(self):
      
        rabi_freq=1.0/(2*self.PI_drive_time)
        print(rabi_freq)
        print(self.volt)
        for i in range(1, len(self.freq_729_dp)):

            try:

                with self.interactive("power calibration "+self.param[i]) as inter:
                    inter.setattr_argument(
                        "rabi_freq",
                        NumberValue(default=rabi_freq*np.sqrt(self.volt[i]), unit="MHz", min=0*MHz, max=240*MHz, precision=8)
                    )
                self.parameter_manager.set_param(
                    self.param[i],
                    inter.rabi_freq,
                    "MHz"
                )

            except Exception:
                pass



        