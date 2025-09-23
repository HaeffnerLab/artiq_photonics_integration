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

        # self.list_of_voltages = [{'DC21': 1.1, 'DC20': 1.0, 'DC19': 1.0, 'DC18': -1.0, 'DC17': 1.0, 'DC16': -1.0, 'DC15': -1.0, 'DC14': -1.0, 'DC13': -1.0, 'DC12': -1.0, 'DC11': -1.0, 'DC10': -1.0, 'DC9': -1.0, 'DC8': -1.0, 'DC7': -1.0, 'DC6': -1.0, 'DC5': -1.0, 'DC4': -1.0, 'DC3': -1.0, 'DC2': -1.0, 'DC1': -1.0}]

        self.list_of_voltages = [{'DC21': 5.177970466120404, 'DC20': -0.30811692898998444, 'DC19': 1.2556000963746698, 'DC18': -0.7276345433939888, 'DC17': 5.52806729534303, 'DC16': 4.771687728620222, 'DC15': 3.6015910934745894, 'DC14': 2.946585567325212, 'DC13': 2.333509284045657, 'DC12': 1.9034959196984427, 'DC10': 6.779450507138272, 'DC9': 3.19520461599525, 'DC8': -0.8152561827142223, 'DC5': 6.1698499344179165, 'DC4': 4.028394785114351, 'DC3': 2.930471683338453, 'DC2': 2.113584906460544, 'DC1': 2.362051741134237, 'DC11': 0.07490107826559261, 'DC7': 0.0, 'DC6': 0.0}]
        
        self.voltage_sets = []
        # Pre-process all voltage sets
        for i, voltage_set in enumerate(self.list_of_voltages):
            # Create a copy to work with
            remapped_voltages = voltage_set.copy()
            
            # Adjust values
            for key, value in remapped_voltages.items():
                if value > 10.0:
                    remapped_voltages[key] = 9.9
                elif value < -10.0:
                    remapped_voltages[key] = -9.9
            
            # Create the voltage array for this set
            voltages = [round(remapped_voltages[f"DC{i}"], 8) for i in range(1, 22)]
            voltages.extend([1.0, 1.1, 0.0])
            # For others, set to 0
            voltages.extend([0.0] * (32 - len(voltages)))
            
            # Add to our list of prepared voltage sets
            self.voltage_sets.append(voltages)
            
            # Print the processed voltage set
            print("Prepared voltage set {}: {}".format(i, voltages))
        
        print("Total prepared voltage sets: {}".format(len(self.voltage_sets)))
        self.index = 0

    @kernel
    def run(self):
        self.core.reset()
        self.core.break_realtime()
        self.zotino0.init()
        delay(10*ms)
        
        # Loop continually through all voltage sets
        while True:
            try:
                for i in range(len(self.voltage_sets)):
                    # Apply this set of voltages
                    voltages = self.voltage_sets[i]
                    self.zotino0.set_dac(voltages, self.channels)
                    print("Applied voltage set")
                    
                    # Wait for 10 seconds before next set
                    delay(30*s)
            except TerminationRequested:
                print("Termination requested")
                break
