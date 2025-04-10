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

        self.remapped_voltages = {'DC21': 0.20633098526749422, 'DC20': -2.6642557672851144, 'DC19': 0.9850898559786229, 'DC18': 0.013088600549954732, 'DC17': -0.3235044483079272, 'DC16': -0.2399026564727407, 'DC15': -0.1963523873789851, 'DC14': -0.16398932073711733, 'DC13': -0.13309311569304247, 'DC12': -0.1133044263703314, 'DC10': -1.0329811243468436, 'DC9': -2.673878713616074, 'DC8': -0.6470500450072192, 'DC7': -0.5678826555173225, 'DC6': -0.3576666685544957, 'DC5': -0.206485091943981, 'DC4': -0.15641822559842772, 'DC3': -0.12118511720025706, 'DC2': -0.0954631627461575, 'DC1': -0.07900979580040766, 'DC11': -0.5387361533488021}

        self.remapped_voltages = {'DC21': 0.07742253423738045, 'DC20': -4.872634265628722, 'DC19': 1.3939286208959107, 'DC18': -0.049577050205133914, 'DC17': -0.6862460246850898, 'DC16': -0.5220758074804206, 'DC15': -0.42846769355065567, 'DC14': -0.3581631684238931, 'DC13': -0.2904224268064113, 'DC12': -0.246930322861226, 'DC10': -2.0932281076330357, 'DC9': -4.951074869080686, 'DC8': -1.4308385959519996, 'DC7': -1.067766867325019, 'DC6': -0.6993276842321339, 'DC5': -0.4169186859933007, 'DC4': -0.31988997933127006, 'DC3': -0.249739862810853, 'DC2': -0.19833950394032662, 'DC1': -0.16550555984462992, 'DC11': -1.0581757855651792}


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
