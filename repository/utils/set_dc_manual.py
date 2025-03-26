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

        self.remapped_voltages = {'DC21': 0.18340532023777265, 'DC20': -2.3682273486978795, 'DC19': 0.8756354275365537, 'DC18': 0.011634311599959762, 'DC17': -0.2875595096070464, 'DC16': -0.2132468057535473, 'DC15': -0.17453545544798676, 'DC14': -0.14576828509965986, 'DC13': -0.11830499172714887, 'DC12': -0.10071504566251681, 'DC10': -0.9182054438638609, 'DC9': -2.3767810787698433, 'DC8': -0.5751555955619726, 'DC7': -0.5047845826820645, 'DC6': -0.3179259276039962, 'DC5': -0.18354230395020532, 'DC4': -0.13903842275415798, 'DC3': -0.10772010417800627, 'DC2': -0.08485614466325112, 'DC1': -0.07023092960036237, 'DC11': -0.47887658075449074}

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
