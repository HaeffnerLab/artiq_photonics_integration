# This is a default experiment that runs when no other experiment is running.
# It sets the outputs to those for trapping correctly so that when experiments finish,
# the system automatically goes back to a stable state.

import time
from artiq.experiment import *

from acf.experiment import _ACFExperiment
from acf_sequences.sequences import sequences
# import serial
class DefaultExperiment(_ACFExperiment):

    def build(self):
        self.setup(sequences)
        self.set_default_scheduling(priority=-99)
        self.seq.ion_store.add_arguments_to_gui()

        #729 dp
        self.add_arg_from_param("frequency/729_dp")
        self.add_arg_from_param("attenuation/729_dp")

        #self.ser= serial.Serial('/dev/serial/by-id/usb-Prolific_Technology_Inc._USB-Serial_Controller_AZBRb132J02-if00-port0', 9600) #//port & baud rate


    def prepare(self):
        self.experiment_data.set_list_dataset("PMT_count", 1, broadcast=True)

    @rpc(flags={"async"})
    def submit_self(self):
        self.scheduler.submit()

    # def turn_off_voltage_source(self):
    #     self.ser.write(b'OUTPut 0\n')

    @kernel
    def run(self):
        self.setup_run()
        self.core.break_realtime()


        #protect ion
        self.seq.ion_store.run()
        delay(5*us)

        #set 729 dp
        self.dds_729_dp.set(self.frequency_729_dp)
        self.dds_729_dp.set_att(self.attenuation_729_dp)
        self.dds_729_dp.sw.off()

        time.sleep(1)
        
        while True:
            #self.seq.ion_store.update_parameters()

            delay(10*ms)

            
            if self.scheduler.check_pause():
                self.submit_self()
                break
            #time.sleep(0.1)
            try:
                #self.turn_off_voltage_source()
                self.core.break_realtime()
                self.ttl_375_pis.off()
                self.ttl_422_pis.off()
            finally:
                pass
            



            self.core.break_realtime()
                
                # with sequential:

                #     if self.enable_diff_mode:
                #         delay(30*us)
                #         self.dds_866_dp.sw.on()

                #         num_pmt_pulses1=self.ttl_pmt_input.count(
                #             self.ttl_pmt_input.gate_rising(self.readout_pmt_sampling_time)
                #         )

                #         delay(30*us)
                #         self.dds_866_dp.sw.off()
                #         delay(30*us)

                #         num_pmt_pulses2=self.ttl_pmt_input.count(
                #             self.ttl_pmt_input.gate_rising(self.readout_pmt_sampling_time)
                #         )

                #         delay(30*us)
                #         num_pmt_pulses = num_pmt_pulses1- num_pmt_pulses2
                #         self.dds_866_dp.sw.on()
                #         delay(10*us)

                #     else:
                #         num_pmt_pulses=self.ttl_pmt_input.count(
                #             self.ttl_pmt_input.gate_rising(self.readout_pmt_sampling_time)
                #         )
                #     self.experiment_data.insert_nd_dataset("PMT_count", 0, num_pmt_pulses)

            delay(50*ms)
