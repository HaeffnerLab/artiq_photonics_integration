# This is a default experiment that runs when no other experiment is running.
# It sets the outputs to those for trapping correctly so that when experiments finish,
# the system automatically goes back to a stable state.

import time
from artiq.experiment import *

from acf.experiment import _ACFExperiment
from acf_sequences.sequences import sequences
import serial
class DefaultExperiment_Camera(_ACFExperiment):

    def build(self):
        self.setup(sequences)
        #self.set_default_scheduling(priority=-99)
        self.seq.ion_store.add_arguments_to_gui()
        self.seq.cam_two_ions.build()

        self.ser= serial.Serial('/dev/serial/by-id/usb-Prolific_Technology_Inc._USB-Serial_Controller_AZBRb132J02-if00-port0', 9600) #//port & baud rate


    def prepare(self):
        self.experiment_data.set_list_dataset("PMT_count", 1, broadcast=True)

    def turn_off_voltage_source(self):
        self.ser.write(b'OUTPut 0\n')

    @kernel
    def run(self):
        self.setup_run()
        self.core.break_realtime()
        self.seq.ion_store.run()
        self.seq.cam_two_ions.cam_setup()
        delay(5*us)

        self.seq.rf.set_voltage('store')

        self.turn_off_voltage_source()
        self.core.break_realtime()       
        
        ################################################################################################################################
        ion_status_detect=1
        ################################################################################################################################
        t=0
        while True:
            self.seq.ion_store.update_parameters()
            if self.scheduler.check_pause():
                self.scheduler.submit()
                break
            self.core.break_realtime()
            try:
               
                self.ttl_375_pis.off()
                self.ttl_422_pis.off()
            finally:
                pass
            
            delay(15*ms)
            
            if ion_status_detect==1 or ion_status_detect==2:
                ion_status_detect=self.seq.cam_two_ions.cam_readout()

                if (ion_status_detect==1): #ion shouldn't move
                    delay(10*ms)
                elif ion_status_detect==2: 
                    self.seq.rf.tickle()
            else:
                self.seq.ion_store.run()
                self.seq.rf.save_ion()
                ion_status_detect=self.seq.cam_two_ions.cam_readout()
                self.seq.ion_store.run()
