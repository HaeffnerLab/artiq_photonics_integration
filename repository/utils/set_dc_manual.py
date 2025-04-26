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
        # self.remapped_voltages = {'DC21': 0.7634702630224153, 'DC20': -2.342491061093222, 'DC19': 1.8134809713341795, 'DC18': -0.2492571975046884, 'DC17': -0.2470888530287279, 'DC16': -0.08989351770786064, 'DC15': -0.06050632152149438, 'DC14': -0.04493959583774859, 'DC13': -0.03496961798189557, 'DC12': -0.029250945822884983, 'DC10': 0.02280719568654499, 'DC9': -2.523512916539453, 'DC8': 0.818238833064853, 'DC7': -0.3784227433818848, 'DC6': -0.27884545014026685, 'DC5': -0.12349466913835971, 'DC4': -0.08311526932142464, 'DC3': -0.05983874948757692, 'DC2': -0.042954240943617106, 'DC1': -0.03181231941285269, 'DC11': -0.42708749402208535}

        list_of_voltages = [{'DC21': -0.08363385436859996, 'DC20': -0.021140147430069218, 'DC19': 0.1053045512595879, 'DC18': 0.3741794984509468, 'DC17': -1.8697205686590848, 'DC16': 1.2140013888404253, 'DC15': -0.09513047670374972, 'DC14': -0.29751131783196777, 'DC13': -0.2907303505967321, 'DC12': -0.19404451306760295, 'DC10': -0.16458545641633912, 'DC9': -0.22519497697334337, 'DC8': -0.2978210507605522, 'DC7': -0.9416501894752036, 'DC6': -1.5102835814617466, 'DC5': -0.6688732157471081, 'DC4': -0.8015028818141172, 'DC3': -0.5694793070215358, 'DC2': -0.3843276500372733, 'DC1': -0.2601574279754737, 'DC11': -0.36060560804365166}]

        self.remapped_voltages = list_of_voltages[0]

        # Print the remapped_voltages
        print("remapped_voltages before refinement:")
        print(self.remapped_voltages)

        # self.voltages = [0.1 - 0.1 * i for i in range(32)]

        # Adjust values
        for key, value in self.remapped_voltages.items():
            if value > 10.0:
                self.remapped_voltages[key] = 9.9
            elif value < -10.0:
                self.remapped_voltages[key] = -9.9

        # Print the remapped_voltages
        print("remapped_voltages after refinement:")
        print(self.remapped_voltages)

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
