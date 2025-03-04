from artiq.experiment import *
from artiq.language.core import  kernel, TerminationRequested

from acf.experiment import _ACFExperiment
from acf_sequences.sequences import sequences
from acf_config.arguments_definition import argument_manager

class SetDCManual(EnvExperiment):       

    def build(self):
        self.setattr_device("core")
        self.setattr_device("zotino0")

        # 32 channels, 0.1 V for first channel, 0.2 V for second channel, ..., 0.32 V for 32nd channel
        self.channels = [i for i in range(32)]
        self.remapped_voltages = {'DC21': -0.2702978228288414, 'DC20': -0.0016379199879436404, 'DC19': 0.7268296023476511, 'DC18': -2.847567351637499, 'DC17': 0.6362017929763644, 'DC16': -0.29941623126263145, 'DC15': -0.29723122277705805, 'DC14': -0.24288624815271403, 'DC13': -0.20197495271243016, 'DC12': -0.17169160199747413, 'DC10': -0.40927858107910453, 'DC9': -0.6060132578614298, 'DC8': -0.7510481418631537, 'DC7': -2.8849917061534995, 'DC6': -0.7371970892274388, 'DC5': -0.4773549312662797, 'DC4': -0.3615053574828117, 'DC3': -0.2615150053900637, 'DC2': -0.19359653726943749, 'DC1': -0.15355269288922646, 'DC11': -0.5715826154293264}
        # self.voltages = [0.1 - 0.1 * i for i in range(32)]

        # For electrode 1 to 21, set the voltages according to the remapped_voltages dictionary, only keep 3 decimal places
        self.voltages = [round(self.remapped_voltages[f"DC{i}"], 8) for i in range(1, 22)]
        self.voltages.extend([1.0, 1.1, 0.0])
        # For others, set to 0
        self.voltages.extend([0.0] * (32 - len(self.voltages)))

        # Print the voltages
        print(self.voltages)
        # Print the length of the voltages
        print(len(self.voltages))
        # Print the type of the voltages and the entire voltages
        print(type(self.voltages))
        print(type(self.voltages[0]))

    @kernel
    def run(self):
        self.core.reset()
        self.core.break_realtime()
        self.zotino0.init()
        delay(10*ms)
        self.zotino0.set_dac(self.voltages, self.channels)
