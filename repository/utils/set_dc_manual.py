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

        self.list_of_voltages = [{'DC21': 1.0, 'DC20': -0.049327010670161514, 'DC19': 0.24571061960570512, 'DC18': 0.8730854963855426, 'DC17': -4.362681326871198, 'DC16': 2.832669907294326, 'DC15': -0.22197111230874927, 'DC14': -0.6941930749412581, 'DC13': -0.6783708180590415, 'DC12': -0.4527705304910735, 'DC10': -0.3840327316381246, 'DC9': -0.5254549462711345, 'DC8': -0.6949157851079553, 'DC7': -2.1971837754421415, 'DC6': -3.523995023410741, 'DC5': -1.5607041700765856, 'DC4': -1.8701733908996068, 'DC3': -1.328785049716917, 'DC2': -0.8967645167536378, 'DC1': -0.6070339986094386, 'DC11': -0.8414130854351871}, {'DC21': 2.0, 'DC20': -0.06342044229020766, 'DC19': 0.31591365377876374, 'DC18': 1.1225384953528401, 'DC17': -5.609161705977255, 'DC16': 3.642004166521276, 'DC15': -0.2853914301112491, 'DC14': -0.8925339534959034, 'DC13': -0.8721910517901963, 'DC12': -0.5821335392028089, 'DC10': -0.49375636924901734, 'DC9': -0.6755849309200301, 'DC8': -0.8934631522816565, 'DC7': -2.824950568425611, 'DC6': -4.53085074438524, 'DC5': -2.0066196472413242, 'DC4': -2.404508645442351, 'DC3': -1.7084379210646072, 'DC2': -1.15298295011182, 'DC1': -0.780472283926421, 'DC11': -1.081816824130955}, {'DC21': 3.0, 'DC20': -0.0775138739102538, 'DC19': 0.38611668795182236, 'DC18': 1.3719914943201381, 'DC17': -6.8556420850833115, 'DC16': 4.451338425748226, 'DC15': -0.3488117479137489, 'DC14': -1.0908748320505486, 'DC13': -1.066011285521351, 'DC12': -0.7114965479145442, 'DC10': -0.6034800068599101, 'DC9': -0.8257149155689256, 'DC8': -1.092010519455358, 'DC7': -3.4527173614090794, 'DC6': -5.5377064653597365, 'DC5': -2.452535124406063, 'DC4': -2.938843899985096, 'DC3': -2.088090792412298, 'DC2': -1.4092013834700023, 'DC1': -0.9539105692434033, 'DC11': -1.3222205628267227}]
        
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
