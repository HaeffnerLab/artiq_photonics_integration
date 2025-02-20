from acf.experiment import _ACFExperiment
from acf_sequences.sequences import sequences
from acf_config.arguments_definition import argument_manager
from artiq.experiment import *
import time
import serial
from acf.utils import get_config_dir
import os
import subprocess

class Load_Ion(_ACFExperiment):
    def build(self):
        self.setup(sequences)

        #self.seq.readout_397.add_arguments_to_gui()s
        self.seq.ion_store.add_arguments_to_gui()

        #self.setattr_device("ttl4") 

        #self.setattr_argument("load_ion", BooleanValue(False))
        self.add_arg_from_param("readout/pmt_sampling_time")
        
        #sudo chmod 666
        # self.ser= serial.Serial('/dev/serial/by-id/usb-Prolific_Technology_Inc._USB-Serial_Controller_AZBRb132J02-if00-port0', 9600) #//port & baud rate


        self.setattr_argument(
            "threshold",
            NumberValue(default=self.parameter_manager.get_param("readout/threshold")+20, precision=0, step=1),
        )

        # self.setattr_argument(
        #     "freq_397_cooling",
        #     NumberValue(default=self.parameter_manager.get_param("frequency/397_cooling"), min=160*MHz, max=250*MHz, unit="MHz", precision=8),  
        # )
        # self.setattr_argument(
        #     "freq_397_far_detuned",
        #     NumberValue(default=self.parameter_manager.get_param("frequency/397_far_detuned"), min=20*MHz, max=250*MHz, unit="MHz", precision=8),
        # )
        # self.setattr_argument(
        #     "attenuation_397",
        #     NumberValue(default=float(self.parameter_manager.get_param("attenuation/397")), min=10*dB, max=30*dB, unit="dB", precision=6)
        # )
        # self.setattr_argument(
        #     "attenuation_397_far_detuned",
        #     NumberValue(default=float(self.parameter_manager.get_param("attenuation/397_far_detuned")), min=10*dB, max=30*dB, unit="dB", precision=6)
        # )

        # self.setattr_argument(
        #     "freq_866_cooling",
        #     NumberValue(default=self.parameter_manager.get_param("frequency/866_cooling"), min=20*MHz, max=250*MHz, unit="MHz", precision=8),  
        # )
        # self.setattr_argument(
        #     "attenuation_866",
        #     NumberValue(default=float(self.parameter_manager.get_param("attenuation/866")), min=5*dB, max=30*dB, unit="dB", precision=6)
        # )

        # Get good cooling params
        #self.freq_397_cooling = float(self.parameter_manager.get_param("frequency/397_cooling"))
        #self.freq_866_cooling = float(self.parameter_manager.get_param("frequency/866_cooling"))
        #self.freq_397_far_detuned = float(self.parameter_manager.get_param("frequency/397_far_detuned"))

        #self.attenuation_397=float(self.parameter_manager.get_param("attenuation/397"))
        #self.attenuation_397_far_detuned=float(self.parameter_manager.get_param("attenuation/397_far_detuned"))
        #self.attenuation_866=float(self.parameter_manager.get_param("attenuation/866"))   

    def prepare(self):
        self.experiment_data.set_list_dataset("PMT_count", 1, broadcast=True)


    #@rpc
    def turn_on_voltage_source(self):
        #Write Current
        self.ser.write(b'CURRent 6.0\n') #Set to 3 A
        #Write Voltage
        self.ser.write(b'VOLTage 4.0\n') #Set to 3 V
        self.ser.write(b'OUTPut 1\n')
    
    #@rpc
    def turn_off_voltage_source(self):
        self.ser.write(b'OUTPut 0\n')

    def submit_default_exp(self):
       
        # exp_file = str(get_config_dir().parent)+ "/repository/default_experiment.py"
    
                
        # run_args = [
        #     "artiq_client",
        #     "submit",
        #     exp_file,
        #     "--class-name",
        #     "DefaultExperiment"
        # ]
        
        # subprocess.run(run_args)

        new_expid = {
            "repo_rev": None, 
            "file": "default_experiment.py",
            "class_name": "DefaultExperiment",
            "arguments": {},
            "log_level": 30,
        }

        self.scheduler.submit(pipeline_name="main", expid=new_expid, priority=-99)
        
    @kernel
    def run(self):
        self.setup_run()
        self.core.break_realtime()

        #turn on the cooling laser
        # self.dds_397_dp.set(self.freq_397_cooling)
        # self.dds_866_dp.set(self.freq_866_cooling)
        # self.dds_397_far_detuned.set(self.freq_397_far_detuned)

        # self.dds_397_dp.set_att(self.attenuation_397)
        # self.dds_397_far_detuned.set_att(self.attenuation_397_far_detuned)
        # self.dds_866_dp.set_att(self.attenuation_866)

        # # self.dds_397_sigma.set(self.freq_397_cooling)
        # # self.dds_397_sigma.set_att(self.attenuation_397)
        # # self.dds_397_sigma.sw.on()

        # self.dds_397_dp.sw.on()
        # self.dds_866_dp.sw.on()
        # self.dds_397_far_detuned.sw.on()

        self.seq.ion_store.run()
        
        self.dds_729_dp.sw.off()
        self.dds_729_sp.sw.off()
        self.dds_854_dp.sw.off()


        

        delay(1*ms)

        # turn on the oven & ttl
        self.ttl_375_pis.on()
        self.ttl_422_pis.on()
        self.turn_on_voltage_source()
        delay(1*s)

        num_pmt_pulses_acc=0

        Time_Out=0

        while True:

            num_pmt_pulses=self.ttl_pmt_input.count(
                self.ttl_pmt_input.gate_rising(self.readout_pmt_sampling_time)
            )

            num_pmt_pulses_acc=int(num_pmt_pulses_acc*0.6+0.4*num_pmt_pulses)

            delay(1*ms)

            #print("current pmt reading:", num_pmt_pulses)
            print("accumulated pmt reading:", num_pmt_pulses_acc)
            self.experiment_data.insert_nd_dataset("PMT_count", 0, num_pmt_pulses)

            delay(0.2*s)

            if num_pmt_pulses_acc>self.threshold:
                self.ttl4.off()
                self.turn_off_voltage_source()           
                break
            
            delay(0.2*s)
            self.ttl_camera_trigger.pulse(10*us)

            Time_Out+=1

            if Time_Out>3600:
                print('Time Out!!!!!!Please Check All the Stuffs!')
                self.ttl4.off()
                self.turn_off_voltage_source()  
                break     
        

        self.ttl_375_pis.off()
        self.ttl_422_pis.off()
        self.turn_off_voltage_source()   
        self.submit_default_exp()



                