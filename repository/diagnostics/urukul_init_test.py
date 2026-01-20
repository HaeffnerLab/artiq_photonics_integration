from artiq.experiment import *


class UrukulInitTest(EnvExperiment):
    def build(self):
        self.setattr_device("core")

        # CPLDs
        self.setattr_device("urukul0_cpld")
        self.setattr_device("urukul1_cpld")
        self.setattr_device("urukul2_cpld")

        # DDS channels
        self.setattr_device("urukul0_ch0")
        self.setattr_device("urukul0_ch1")
        self.setattr_device("urukul0_ch2")
        self.setattr_device("urukul0_ch3")
        self.setattr_device("urukul1_ch0")
        self.setattr_device("urukul1_ch1")
        self.setattr_device("urukul1_ch2")
        self.setattr_device("urukul1_ch3")
        self.setattr_device("urukul2_ch0")
        self.setattr_device("urukul2_ch1")
        self.setattr_device("urukul2_ch2")
        self.setattr_device("urukul2_ch3")

        self.setattr_argument(
            "board",
            NumberValue(default=0, min=0, max=2, step=1, precision=0),
            tooltip="Urukul board index (0, 1, 2)"
        )
        self.setattr_argument(
            "channel",
            NumberValue(default=-1, min=-1, max=3, step=1, precision=0),
            tooltip="DDS channel (0-3), or -1 for all channels"
        )
        self.setattr_argument(
            "cpld_first",
            BooleanValue(True),
            tooltip="Initialize CPLD before DDS channels"
        )

    @kernel
    def init_board0(self):
        if self.cpld_first:
            self.urukul0_cpld.init()
        if self.channel == -1 or self.channel == 0:
            self.urukul0_ch0.init()
        if self.channel == -1 or self.channel == 1:
            self.urukul0_ch1.init()
        if self.channel == -1 or self.channel == 2:
            self.urukul0_ch2.init()
        if self.channel == -1 or self.channel == 3:
            self.urukul0_ch3.init()
        if not self.cpld_first:
            self.urukul0_cpld.init()

    @kernel
    def init_board1(self):
        if self.cpld_first:
            self.urukul1_cpld.init()
        if self.channel == -1 or self.channel == 0:
            self.urukul1_ch0.init()
        if self.channel == -1 or self.channel == 1:
            self.urukul1_ch1.init()
        if self.channel == -1 or self.channel == 2:
            self.urukul1_ch2.init()
        if self.channel == -1 or self.channel == 3:
            self.urukul1_ch3.init()
        if not self.cpld_first:
            self.urukul1_cpld.init()

    @kernel
    def init_board2(self):
        if self.cpld_first:
            self.urukul2_cpld.init()
        if self.channel == -1 or self.channel == 0:
            self.urukul2_ch0.init()
        if self.channel == -1 or self.channel == 1:
            self.urukul2_ch1.init()
        if self.channel == -1 or self.channel == 2:
            self.urukul2_ch2.init()
        if self.channel == -1 or self.channel == 3:
            self.urukul2_ch3.init()
        if not self.cpld_first:
            self.urukul2_cpld.init()

    @kernel
    def run(self):
        self.core.reset()
        self.core.break_realtime()

        if self.board == 0:
            self.init_board0()
        elif self.board == 1:
            self.init_board1()
        elif self.board == 2:
            self.init_board2()
