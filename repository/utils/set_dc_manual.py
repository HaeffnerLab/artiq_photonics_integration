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

        # self.list_of_voltages = [{'DC12': -0.6206902556739394, 'DC21': -1.1022211249592764, 'DC20': -1.1348286755026922, 'DC19': 2.784226752812928, 'DC18': -5.502326653709042, 'DC17': 1.194017497002936, 'DC16': 1.1659314109113068, 'DC15': 0.2719000687005087, 'DC14': -0.09026643293922579, 'DC13': -0.21259465805606834, 'DC9': -1.1743543329867876, 'DC6': -1.4954784582995182, 'DC10': -1.9317569211185273, 'DC8': 0.0, 'DC7': 0.0, 'DC11': -3.1738809768978875, 'DC4': -1.0832987764314947, 'DC1': -0.6813522383679972, 'DC3': -0.4995585781707656, 'DC2': -0.4018516645097744, 'DC5': -1.0788882998684302}]

        # self.list_of_voltages = [{'DC21': -9.99, 'DC20': -9.0, 'DC19': -8.0, 'DC18': -7.0, 'DC17': -6.0, 'DC16': -5.0, 'DC15': -4.0, 'DC14': -3.0, 'DC13': -2.0, 'DC12': -1.0, 'DC10': +1.0, 'DC9': +2.0, 'DC8': +3.0, 'DC7': +4.0, 'DC6': +5.0, 'DC5': +6.0, 'DC4': +7.0, 'DC3': +8.0, 'DC2': +9.0, 'DC1': +9.99, 'DC11': +0.75}]

        self.list_of_voltages = [{'DC21': 0.08279405523957592, 'DC20': 0.14743453549648433, 'DC19': 0.19739336393733184, 'DC18': 0.5590622458046118, 'DC17': 2.1045690063035236, 'DC16': 0.19675754871276957, 'DC15': -3.164945157486676, 'DC14': 2.2828587108915026, 'DC13': 1.460909661518466, 'DC12': 0.7317061206668081, 'DC10': 0.08691966611132357, 'DC9': 0.1268113535180908, 'DC8': 0.15407863457544582, 'DC7': 0.3332871831531816, 'DC6': 1.005886862797341, 'DC5': -0.5796256876303845, 'DC4': -2.088355631417253, 'DC3': 0.5551746302279933, 'DC2': 0.6959437209647512, 'DC11': -0.26365233213793193, 'DC1': 0.0}]
        
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
