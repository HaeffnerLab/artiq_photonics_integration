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

        self.remapped_voltages = {'DC21': -0.22302361164959988, 'DC20': -0.056373726480184586, 'DC19': 0.2808121366922344, 'DC18': 0.9978119958691913, 'DC17': -4.985921516424226, 'DC16': 3.2373370369078005, 'DC15': -0.2536812712099992, 'DC14': -0.7933635142185808, 'DC13': -0.7752809349246189, 'DC12': -0.5174520348469412, 'DC10': -0.43889455044357095, 'DC9': -0.6005199385955823, 'DC8': -0.7941894686948059, 'DC7': -2.511067171933876, 'DC6': -4.027422883897991, 'DC5': -1.7836619086589547, 'DC4': -2.1373410181709787, 'DC3': -1.518611485390762, 'DC2': -1.024873733432729, 'DC1': -0.6937531412679298, 'DC11': -0.961614954783071}

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
