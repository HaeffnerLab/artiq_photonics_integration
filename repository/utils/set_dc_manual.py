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

        self.list_of_voltages = [
            # {'DC21': 0.04367947637940177, 'DC20': 0.02449257058984275, 'DC19': 0.41519301995974, 'DC18': 0.23258385049031943, 'DC17': 1.1593774592869284, 'DC16': 2.726311488492673, 'DC15': -2.753747788771533, 'DC14': -1.530325025380511, 'DC13': 3.2496089400954435, 'DC12': 1.8670492845185227, 'DC10': 0.0448380206890515, 'DC9': 0.050920423034254494, 'DC8': 0.05795636916409533, 'DC7': 0.10200393206545866, 'DC6': 0.4056439521057499, 'DC5': 0.5682943231624529, 'DC4': -1.9201678463152883, 'DC3': -1.4769761673642692, 'DC2': 1.3552932044700015, 'DC11': -0.3160990344107006, 'DC1': 0.0},
        
        
        # {'DC21': 0.2397259657802227, 'DC20': 0.3355969353013055, 'DC19': 0.43101414725880616, 'DC18': 0.863591906909872, 'DC17': 1.9910736517920067, 'DC16': 2.634953938331349, 'DC15': -0.2268934038958248, 'DC14': -2.287162074534368, 'DC13': 3.6393767332393816, 'DC12': 2.7367867301386677, 'DC10': 0.34549951631217385, 'DC9': 0.44661080455477575, 'DC8': 0.5491013060358161, 'DC7': 0.991218093174095, 'DC6': 2.010582626586247, 'DC5': 2.1586093983070898, 'DC4': -0.5458311108239576, 'DC3': -1.661743859982539, 'DC2': 2.9182220907073493, 'DC11': -0.08444825767939342, 'DC1': 0.0},

        {'DC21': 0.23106240822792154, 'DC20': 0.32747871790985755, 'DC19': 0.42306869948138176, 'DC18': 0.8630068707523366, 'DC17': 2.0913948102046813, 'DC16': 2.841265653522486, 'DC15': -0.8156515264176433, 'DC14': -2.0453648801240396, 'DC13': 3.881735798928065, 'DC12': 2.7600533817558683, 'DC10': 0.3257634539408675, 'DC9': 0.42055090977405696, 'DC8': 0.5158797821007379, 'DC7': 0.909584402418573, 'DC6': 1.9151575763817235, 'DC5': 1.997523444642741, 'DC4': -0.8962653208187612, 'DC3': -1.4279056491373834, 'DC2': 2.8883359021897563, 'DC11': -0.10158862475548221, 'DC1': 0.0}

        ]
        
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
