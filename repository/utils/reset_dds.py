from artiq.experiment import *

class ResetDDS(EnvExperiment):
    def build(self):
        self.setattr_device("core")
        self.dv=[]

        for board in range(0,3):
            for channel in range(4):
                self.setattr_device(f"urukul{board}_ch{channel}")      
                eval(f"self.dv.append(self.urukul{board}_ch{channel})")
    @kernel
    def run(self):
        self.core.reset()
        self.core.break_realtime()

        for _ in self.dv:
            _.init()
            _.sw.off()
