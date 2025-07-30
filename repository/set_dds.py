from artiq.experiment import *

from acf.experiment import _ACFExperiment
from acf_sequences.sequences import sequences
from acf_config.arguments_definition import argument_manager

class SetDDS(_ACFExperiment):
    def build(self):
        self.setup(sequences)
        self.seq.ion_store.add_arguments_to_gui()


        # Frequency parameters
        self.add_arg_from_param("frequency/397_resonance")
        self.add_arg_from_param("frequency/397_cooling")
        self.add_arg_from_param("frequency/397_far_detuned")
        self.add_arg_from_param("frequency/397_sigma")
        self.add_arg_from_param("frequency/866_cooling")
        self.add_arg_from_param("frequency/729_dp")
        self.add_arg_from_param("frequency/729_sp")
        self.add_arg_from_param("frequency/729_sp_aux")
        self.add_arg_from_param("frequency/854_dp")
        self.add_arg_from_param("frequency/RF")

        # Attenuation parameters
        self.add_arg_from_param("attenuation/397")
        self.add_arg_from_param("attenuation/397_sigma")
        self.add_arg_from_param("attenuation/397_far_detuned")
        self.add_arg_from_param("attenuation/866")
        self.add_arg_from_param("attenuation/729_dp")
        self.add_arg_from_param("attenuation/729_sp")
        self.add_arg_from_param("attenuation/854_dp")
        self.add_arg_from_param("attenuation/RF")

        # Readout parameters
        self.add_arg_from_param("readout/pmt_sampling_time")


        # Laser control checkboxes
        self.setattr_argument("enable_729", BooleanValue(False), group='Laser Control')
        self.setattr_argument("enable_397", BooleanValue(True), group='Laser Control')
        self.setattr_argument("enable_866", BooleanValue(True), group='Laser Control')
        self.setattr_argument("enable_854", BooleanValue(False), group='Laser Control')
        self.setattr_argument("enable_rf", BooleanValue(False), group='Laser Control')
        self.setattr_argument("enable_raman", BooleanValue(False), group='Laser Control')
        self.setattr_argument("enable_729_radial", BooleanValue(False), group='Laser Control')


    def prepare(self):
        self.experiment_data.set_list_dataset("PMT_count", 1, broadcast=True)

    @kernel
    def run(self):  
        self.setup_run()
        self.core.break_realtime()

        # Protect ion
        self.seq.ion_store.run()
        delay(5*us)

        # =============== 729 nm Laser Control ===============
        if self.enable_729:
            self.dds_729_dp.set_att(self.attenuation_729_dp)
            self.dds_729_sp.set_att(self.attenuation_729_sp)
            self.dds_729_sp_aux.set_att(self.attenuation_729_sp)

            self.dds_729_dp.set(self.frequency_729_dp)
            self.dds_729_sp.set(self.frequency_729_sp)
            self.dds_729_sp_aux.set(self.frequency_729_sp_aux)

            self.dds_729_dp.sw.on()
            self.dds_729_sp.sw.on()
            self.dds_729_sp_aux.sw.off()

        # =============== 397 nm Laser Control ===============
        if self.enable_397:
            self.dds_397_sigma.set(self.frequency_397_sigma)
            self.dds_397_dp.set(self.frequency_397_cooling)
            self.dds_397_far_detuned.set(self.frequency_397_far_detuned)

            self.dds_397_dp.set_att(self.attenuation_397)
            self.dds_397_far_detuned.set_att(self.attenuation_397_far_detuned)
            self.dds_397_sigma.set_att(self.attenuation_397_sigma)

            self.dds_397_dp.sw.on()
            self.dds_397_far_detuned.sw.on()
            self.dds_397_sigma.sw.on()

        # =============== 866 nm Laser Control ===============
        if self.enable_866:
            self.dds_866_dp.set(self.frequency_866_cooling)
            self.dds_866_dp.set_att(self.attenuation_866)
            self.dds_866_dp.sw.on()

        # =============== 854 nm Laser Control ===============
        if self.enable_854:
            self.dds_854_dp.set(self.frequency_854_dp)
            self.dds_854_dp.set_att(self.attenuation_854_dp)
            
            self.dds_854_dp.sw.on()
        else:
            self.dds_854_dp.sw.off()

        # =============== RF Control ===============
        # if self.enable_rf:
        #     self.dds_rf_g_qubit.set(self.frequency_RF)
        #     self.dds_rf_g_qubit.set_att(self.attenuation_RF)
        #     self.dds_rf_g_qubit.sw.on()

        # =============== Raman Control ===============
        if self.enable_raman:
            self.dds_Raman_1.set(120*MHz)
            self.dds_Raman_1.set_att(20*dB)
            self.dds_Raman_2.set(103*MHz)
            self.dds_Raman_2.set_att(20*dB)
            self.dds_Raman_1.sw.on()
            self.dds_Raman_2.sw.on()

        # =============== 729 Radial Control ===============
        if self.enable_729_radial:
            self.dds_729_radial_sp.set_att(10*dB)
            self.dds_729_radial_dp.set_att(10*dB)
            self.dds_729_radial_sp_aux.set_att(10*dB)
            
            self.dds_729_radial_sp.set(self.frequency_729_sp)
            self.dds_729_radial_dp.set(self.frequency_729_dp)
            self.dds_729_radial_sp_aux.set(self.frequency_729_sp_aux+10.*MHz)
            
            self.dds_729_radial_dp.sw.on()
            self.dds_729_radial_sp.cfg_sw(True)
            self.dds_729_radial_sp_aux.cfg_sw(False)

        # Main loop
        while True:
            self.core.break_realtime()
            delay(10*ms)

            with parallel:
                if self.scheduler.check_pause():
                    self.scheduler.submit()
                    break

            delay(100*ms)

