from acf.experiment import _ACFExperiment
from acf_sequences.sequences import sequences
from acf_config.arguments_definition import argument_manager

from artiq.experiment import *

from acf.function.fitting import *
from artiq.coredevice.ad9910 import (RAM_DEST_ASF, RAM_MODE_BIDIR_RAMP, RAM_MODE_RAMPUP, PHASE_MODE_TRACKING , PHASE_MODE_ABSOLUTE)

class Test729Sp(_ACFExperiment):
    def build(self):
        self.setup(sequences)

        self.setattr_argument(
            "phase",
            NumberValue(default=0.0, min=0.0, max=30, precision=8)
        )
    
    @kernel
    def run(self):

        self.setup_run()
        self.seq.ion_store.run()
        self.core.break_realtime()

        self.dds_729_sp_aux.set(80*MHz)
        self.dds_729_sp.set(80*MHz, phase= self.phase)

        self.dds_729_sp.set_phase_mode(PHASE_MODE_ABSOLUTE)
        self.dds_729_sp_aux.set_phase_mode(PHASE_MODE_ABSOLUTE)

        self.dds_729_sp.sw.on()
        self.dds_729_sp_aux.sw.on()

        while True:
            pass
        # #turn off all dds
        # self.seq.off_dds.run()
        # delay(5*us)

        # self.dds_729_sp.set_phase_mode(PHASE_MODE_ABSOLUTE)
        # self.dds_729_sp_aux.set_phase_mode(PHASE_MODE_ABSOLUTE)

        # self.dds_729_sp.sw.off()
        # self.dds_729_sp_aux.sw.off()

        # at_mu(now_mu() & ~7)
        # start_time_mu = now_mu()

        # delay(2*s)

        # self.dds_729_sp.set_att(5*dB)
        # self.dds_729_sp_aux.set_att(5*dB)
        # delay(50*us)
        
        # while True:
        #     self.dds_729_sp.set(80.5*MHz,phase=0.0)#,ref_time_mu=start_time_mu)
        #     self.dds_729_sp_aux.set(79.5*MHz,phase=0.)#,ref_time_mu=start_time_mu)
        #     delay(5*us)

        #     self.dds_729_sp.sw.on()
        #     self.dds_729_sp_aux.sw.on()
        #     delay(10*us)
        #     self.dds_729_sp.sw.off()
        #     self.dds_729_sp_aux.sw.off()

        #     delay(10*us)
        #     self.dds_729_sp.set(80.*MHz,phase=0.0)#,ref_time_mu=start_time_mu)
        #     delay(1*us)
        #     self.dds_729_sp_aux.set(80.0*MHz,phase=0.)#,ref_time_mu=start_time_mu)
        #     delay(10*us)

        #     self.dds_729_sp.set(84.*MHz,phase=0.0)#,ref_time_mu=start_time_mu)
        #     delay(1*us)
        #     self.dds_729_sp_aux.set(92.0*MHz,phase=0.)#,ref_time_mu=start_time_mu)
        #     delay(100*us)

        #     self.dds_729_sp.set(80.5*MHz,phase=0.0)#,ref_time_mu=start_time_mu)
        #     self.dds_729_sp_aux.set(79.5*MHz,phase=0.2)#,ref_time_mu=start_time_mu)
        #     delay(5*us)

        #     self.dds_729_sp.sw.on()
        #     self.dds_729_sp_aux.sw.on()
        #     delay(10*us)
        #     self.dds_729_sp.sw.off()
        #     self.dds_729_sp_aux.sw.off()
        
        #     delay(10*us)
