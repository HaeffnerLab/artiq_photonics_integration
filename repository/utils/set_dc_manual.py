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

        self.list_of_voltages = [{'DC21': -9.55798327595937, 'DC20': 4.172503688832631, 'DC19': -1.976238136412831, 'DC18': -1.1509324656674633, 'DC17': 8.414093015698924, 'DC16': -3.397217629419453, 'DC15': -3.232700340651789, 'DC14': -3.0652743297417713, 'DC13': -2.5944594696769725, 'DC12': -2.2092402653164083, 'DC10': -9.814930651042218, 'DC9': 6.652911008756076, 'DC8': -4.52971644149379, 'DC5': -5.7107970712433955, 'DC4': -3.6852649649133533, 'DC3': -2.9493918259202454, 'DC2': -2.123609360116291, 'DC1': -4.078319101527683, 'DC11': -0.2519408547522847, 'DC7': 0.0, 'DC6': 0.0}]
        
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
