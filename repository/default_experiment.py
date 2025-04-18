# This is a default experiment that runs when no other experiment is running.
# It sets the outputs to those for trapping correctly so that when experiments finish,
# the system automatically goes back to a stable state.

import time
from artiq.experiment import *

from acf.experiment import _ACFExperiment
from acf_sequences.sequences import sequences
class DefaultExperiment(_ACFExperiment):

    def build(self):
        self.setup(sequences)
        self.set_default_scheduling(priority=-99)
        self.seq.ion_store.add_arguments_to_gui()
        self.seq.readout_397.add_arguments_to_gui()


        self.setattr_argument("enable_diff_mode", BooleanValue(False))

        self.setattr_argument("enable_397_far_detuned", BooleanValue(True))

       # self.add_arg_from_param("readout/pmt_sampling_time")
                #sudo chmod 666



        # Get good cooling params
        # self.freq_397_cooling = float(self.parameter_manager.get_param("frequency/397_cooling"))
        # self.freq_866_cooling = float(self.parameter_manager.get_param("frequency/866_cooling"))
        # self.freq_397_far_detuned = float(self.parameter_manager.get_param("frequency/397_far_detuned"))

        # self.attenuation_397=float(self.parameter_manager.get_param("attenuation/397"))
        # self.attenuation_397_far_detuned=float(self.parameter_manager.get_param("attenuation/397_far_detuned"))
        # self.attenuation_866=float(self.parameter_manager.get_param("attenuation/866"))   

    def prepare(self):
        self.experiment_data.set_list_dataset("PMT_count", 1, broadcast=True)

    # def turn_off_voltage_source(self):
    #     self.ser.write(b'OUTPut 0\n')

    @kernel
    def run(self):
        self.setup_run()
        self.core.break_realtime()


        #protect ion
        self.seq.ion_store.run()
        delay(5*us)

        # if not self.enable_397_far_detuned:
        #     self.self.dds_397_far_detuned.sw.off()


        
        # Loop forever. If an experiment is detected with higher priority, submit this experiment again and exit
        while True:
            # self.seq.ion_store.update_parameters()
            self.core.break_realtime()
            self.seq.ion_store.run()
            delay(10*ms)

            with parallel:
                if self.scheduler.check_pause():
                    self.scheduler.submit()
                    break
                #time.sleep(0.1)
                # try:
                #     self.turn_off_voltage_source()
                #     self.ttl_375_pis.off()
                #     self.ttl_422_pis.off()
                # finally:
                #     pass
                self.core.break_realtime()
                    
                num_pmt_pulses=self.seq.readout_397.run()

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
                self.experiment_data.insert_nd_dataset("PMT_count", 0, num_pmt_pulses)

                self.core.break_realtime()

            delay(50*ms)
