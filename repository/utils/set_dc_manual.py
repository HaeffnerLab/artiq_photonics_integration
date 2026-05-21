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

            # {'DC21': 0.03969789286734213, 'DC20': -0.052064015569175795, 'DC19': 0.00732420852577337, 'DC18': -0.5388336039054585, 'DC17': -3.343215361092149, 'DC16': -0.6192149315798945, 'DC15': -0.020475195739602308, 'DC14': -0.0681837961441197, 'DC13': -0.1290959834375677, 'DC12': -0.17846505792850548, 'DC10': -0.45327171805035615, 'DC9': -0.3290767342247377, 'DC8': -0.3710695588924077, 'DC7': -0.36674797468590603, 'DC6': -2.4419266779941387, 'DC5': -0.4964278144601906, 'DC4': -0.21991079300721433, 'DC3': -0.256133530174313, 'DC2': -0.22849543662021735, 'DC1': 0.0, 'DC11': -0.4104479774348195}

            {'DC21': -0.12125493154560572, 'DC20': -0.0274416956921315, 'DC19': 0.10505608697391161, 'DC18': 1.0145639476253476, 'DC17': 2.763706571726557, 'DC16': -0.15739809213282183, 'DC15': -8.059682748336375, 'DC14': -13.381498523995088, 'DC13': -5.367665231446927, 'DC12': 0.9623212889797859, 'DC10': -0.7026674986395961, 'DC9': -0.7858695513177798, 'DC8': -0.4252041210900361, 'DC7': -0.054228629207309406, 'DC6': 0.16079461982975052, 'DC5': -1.1254465640086506, 'DC4': -5.798042007293648, 'DC3': -9.719293988904049, 'DC2': -3.21621013367794, 'DC1': 1.1515710315777763, 'DC11': -1.4758429412830611}


        ]

        #========================================
        # TEMPORARY SOLUTION!!!!!!!!!!!!!!!!!!!!!!!

        temp_voltage_dict_list = []

        for voltage_dict in self.list_of_voltages:
            new_voltage_dict = {}
            for electrode_name, voltage_value in voltage_dict.items():
                new_voltage_dict[electrode_name] = voltage_value/5.0
            temp_voltage_dict_list.append(new_voltage_dict)
        
        self.list_of_voltages = temp_voltage_dict_list

        #========================================
        
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
