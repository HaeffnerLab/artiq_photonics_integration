from artiq.experiment import *

from acf.experiment import _ACFExperiment
from acf_sequences.sequences import sequences
from acf_config.arguments_definition import argument_manager

class SetDDS(_ACFExperiment):
    def build(self):
        self.setup(sequences)
        self.seq.ion_store.add_arguments_to_gui()

        self.add_arg_from_param("frequency/397_resonance")
        self.add_arg_from_param("frequency/397_cooling")
        self.add_arg_from_param("frequency/397_far_detuned")
        self.add_arg_from_param("frequency/397_sigma")
        self.add_arg_from_param("frequency/866_cooling")
  
        self.add_arg_from_param("frequency/729_dp")
        self.add_arg_from_param("frequency/729_sp")
        self.add_arg_from_param("frequency/729_sp_aux")
        self.add_arg_from_param("frequency/854_dp")

        self.add_arg_from_param("attenuation/397")
        self.add_arg_from_param("attenuation/397_sigma")
        self.add_arg_from_param("attenuation/397_far_detuned")
        self.add_arg_from_param("attenuation/866")
        self.add_arg_from_param("attenuation/729_dp")
        self.add_arg_from_param("attenuation/729_sp")
      
        self.add_arg_from_param("attenuation/854_dp")

        self.add_arg_from_param("attenuation/RF")
        self.add_arg_from_param("frequency/RF")

        self.add_arg_from_param("readout/pmt_sampling_time")

    def prepare(self):
        self.experiment_data.set_list_dataset("PMT_count", 1, broadcast=True)

    @kernel
    def run(self):  
        self.setup_run()
        self.core.break_realtime()

        #protect ion
        self.seq.ion_store.run()
        delay(5*us)
        ###################################################################### 729
        
        # self.dds_729_dp.set_att(self.attenuation_729_dp)
        # self.dds_729_sp.set_att(self.attenuation_729_sp)
        # self.dds_729_sp_aux.set_att(self.attenuation_729_sp)

        # self.dds_729_dp.set(self.frequency_729_dp)
        # self.dds_729_sp.set(self.frequency_729_sp)
        # self.dds_729_sp_aux.set(self.frequency_729_sp_aux)

        # self.dds_729_dp.sw.on()
        # self.dds_729_sp.sw.on()
        # self.dds_729_sp_aux.sw.off()
        

        ###################################################################### 397

        # self.dds_397_sigma.set(self.frequency_397_sigma)
        # self.dds_397_dp.set(self.frequency_397_cooling)
        # self.dds_397_far_detuned.set(self.frequency_397_far_detuned)
        # self.dds_397_sigma.set(self.frequency_397_sigma)

        # self.dds_397_dp.set_att(self.attenuation_397)
        # self.dds_397_far_detuned.set_att(self.attenuation_397_far_detuned)
        # self.dds_397_sigma.set_att(self.attenuation_397_sigma)

        # self.dds_397_dp.sw.on()
        # self.dds_397_far_detuned.sw.on()
        # self.dds_397_sigma.sw.on()


        # #############
        # self.dds_rf_g_qubit.set(80*MHz)
        # self.dds_rf_g_qubit.set_att(20*dB)
        # self.dds_rf_g_qubit.sw.on()


        #######################################################################  866
        # self.dds_866_dp.set(self.frequency_866_cooling)
        # self.dds_866_dp.set_att(self.attenuation_866)
        # self.dds_866_dp.sw.off()

        ######################################################################  854
        # self.dds_866_dp.sw.off()
        # self.dds_854_dp.set(self.frequency_854_dp)
        # self.dds_854_dp.set_att(11*dB)
        # self.dds_854_dp.sw.on()

        ######################################################################  729
        self.dds_729_dp.set_att(self.attenuation_729_dp)
        self.dds_729_sp.set_att(self.attenuation_729_sp)
        self.dds_729_dp.set(self.frequency_729_dp)
        self.dds_729_sp.set(self.frequency_729_sp)
        self.dds_729_dp.sw.on()
        self.dds_729_sp.sw.on()

        # self.ttl_rf_switch_AWG_729SP.off()
        # self.ttl_rf_switch_DDS_729SP.on()
        # self.ttl_rf_switch_DDS_729SP.output()

        # self.seq.readout_397.run()


        # # set attenuation
        # self.dds_397_dp.set_att(self.attenuation_397)
        # self.dds_397_far_detuned.set_att(self.attenuation_397_far_detuned)
        # self.dds_866_dp.set_att(self.attenuation_866)
        # self.dds_854_dp.set_att(self.attenuation_854_dp)
        # #self.dds_866_addressing.set_att(self.attenuation_866_addressing)
        
        # #self.dds_729_sp_aux.set_att(self.attenuation_729_sp_aux)

        # self.dds_rf_g_qubit.set_att(self.attenuation_RF)


        # # set frequency and phase

        # self.dds_397_dp.set(self.frequency_397_cooling)
        # self.dds_397_far_detuned.set(self.frequency_397_far_detuned)
        # self.dds_866_dp.set(self.frequency_866_cooling)
        # self.dds_854_dp.set(self.frequency_854_dp)
        # #self.dds_866_addressing.set(self.freq_866_addressing)
        # self.dds_729_dp.set(self.frequency_729_dp)
        # self.dds_729_sp.set(self.frequency_729_sp, 0.0)#self.phase_729_sp)
        # #self.dds_729_sp_aux.set(self.freq_729_sp_aux,phase = self.phase_729_sp_aux)
        # #self.dds_rf_g_qubit.set(self.freq_rf_g_qubit)

        # self.dds_rf_g_qubit.set(self.frequency_RF)

        # # set phase

        # #self.dds_729_sp.set_phase(self.phase_729_sp)
        # #self.dds_729_sp_aux.set_phase(self.phase_729_sp_aux)

        # self.dds_854_dp.set_att(30*dB)

        # # turn devices on
        # self.dds_397_dp.sw.on()
        # self.dds_397_far_detuned.sw.on()
        # self.dds_866_dp.sw.on()
        # self.dds_854_dp.sw.on()
        # delay(2*ms)
        # #self.dds_866_addressing.sw.on()
        # self.dds_729_dp.sw.on()
        # self.dds_729_sp.sw.on()
        # delay(2*ms)
        # self.dds_729_sp_aux.sw.off()
        # self.dds_rf_g_qubit.sw.off()
        

         
        # # Loop forever. If an experiment is detected with higher priority, submit this experiment again and exit
        while True:
            self.core.break_realtime()
            delay(10*ms)

            with parallel:
                if self.scheduler.check_pause():
                    self.scheduler.submit()
                    break
                #time.sleep(0.1)
                with sequential:
                    num_pmt_pulses=self.ttl_pmt_input.count(
                        self.ttl_pmt_input.gate_rising(self.readout_pmt_sampling_time)
                    )
                    self.experiment_data.insert_nd_dataset("PMT_count", 0, num_pmt_pulses)

            delay(100*ms)

