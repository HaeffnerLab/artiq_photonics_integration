from acf.sequence import Sequence

from artiq.experiment import kernel, delay, s, dB, us, NumberValue, MHz, ms
from numpy import int32, int64

class RF(Sequence):

    def __init__(self):
        super().__init__()

        # -3.0  -- -2.0 original
        # -2.5  -- -1.67
        # -2.0  -- -1.34 (-1.6 phase separation)

        factor = 3.0/2.0

        #for trap output -11dBm 
        # self.rf_store = -2.0*factor # Option 0 "store"
        # self.rf_dump = -1.8*factor  # Option 1 "dump"
        # self.rf_load = -1.5*factor   # Option 2 "load"
        # self.rf_save = -1.5*factor   # Option 3 "save"


        #for -9dBm
        self.rf_store = -0.0*factor # Option 0 "store"
        self.rf_dump = -2.3*factor  # Option 1 "dump"
        self.rf_load = - 1.8*factor   # Option 2 "load"
        self.rf_save = -2.1*factor   # Option 3 "save"

        #for -9dbm single ion
        # self.rf_store = -1.9*factor # Option 0 "store"
        # self.rf_dump = -2.2*factor  # Option 1 "dump"
        # self.rf_load = -1.9*factor   # Option 2 "load"
        # self.rf_save = -1.9*factor   # Option 3 "save"

        self.rf_bias= 1.0

    @kernel
    def set_voltage(self,
            mode="store"
        ):

        pass

        # if mode=="load":
        #     self.dac.write_dac(2, self.rf_bias)
        #     self.dac.write_dac(3, self.rf_bias)
        #     self.dac.write_dac(0, self.rf_load)
        #     self.dac.write_dac(1, self.rf_load)
        #     self.dac.load()
        # elif mode=="dump":
        #     self.dac.write_dac(2, 5.0)
        #     self.dac.write_dac(3, 5.0)
        #     self.dac.write_dac(0, self.rf_dump)
        #     self.dac.write_dac(1, self.rf_dump)
        #     self.dac.load()
        # elif mode=="store":
        #     self.dac.write_dac(2, self.rf_bias)
        #     self.dac.write_dac(3, self.rf_bias)
        #     self.dac.write_dac(0, self.rf_store)
        #     self.dac.write_dac(1, self.rf_store)
        #     self.dac.load()
        # elif mode=="save":
        #     self.dac.write_dac(2, self.rf_bias)
        #     self.dac.write_dac(3, self.rf_bias)
        #     self.dac.write_dac(0, self.rf_save)
        #     self.dac.write_dac(1, self.rf_save)
        #     self.dac.load()
        # elif mode=="lower":
        #     self.dac.write_dac(2, self.rf_bias)
        #     self.dac.write_dac(3, self.rf_bias)
        #     self.dac.write_dac(0, -1.0)
        #     self.dac.write_dac(1, -1.0)
        #     self.dac.load()       

    @kernel
    def tickle(self, pulse_time=20.0*ms):
        pass

        # self.dac.write_dac(2, self.rf_bias)
        # self.dac.write_dac(3, self.rf_bias)

        # self.dac.write_dac(0, self.rf_dump)
        # self.dac.write_dac(1, self.rf_dump)
        # self.dac.load()
        # delay(pulse_time)
        # self.dac.write_dac(0, self.rf_store)
        # self.dac.write_dac(1, self.rf_store)
        # self.dac.load()
        # delay(100.0*ms)

    @kernel
    def save_ion(self):
        pass

        # self.dac.write_dac(2, self.rf_bias)
        # self.dac.write_dac(3, self.rf_bias)
        # self.dac.write_dac(0, self.rf_save)
        # self.dac.write_dac(1, self.rf_save)
        # self.dac.load()
        # delay(600*ms)
        # self.dac.write_dac(0, self.rf_store)
        # self.dac.write_dac(1, self.rf_store)
        # self.dac.load()
        # delay(500.0*ms)