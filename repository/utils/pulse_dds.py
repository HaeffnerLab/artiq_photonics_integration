from artiq.experiment import *
from artiq.language.core import  kernel, TerminationRequested

from acf.experiment import _ACFExperiment
from acf_sequences.sequences import sequences
from acf_config.arguments_definition import argument_manager

class PulseDDS(_ACFExperiment):       

    def build(self):
        self.setattr_device("core")
        self.setattr_device("zotino0")  # Add zotino0 device for DC control
        self.setup(sequences)

        self.setattr_argument(
            "if_pulse",
            BooleanValue(default=True),
            tooltip="Is pulsing effect on"
        )

        self.setattr_argument(
            "on_secs",
            NumberValue(default=0.2*s, unit="s", min=0*s, precision=8),
            tooltip="Seconds on"
        )

        self.setattr_argument(
            "off_secs",
            NumberValue(default=0.2*s, unit="s", min=0*s, precision=8),
            tooltip="Seconds off"
        )

        self.setattr_argument(
            "scan_dc_voltages",
            BooleanValue(default=True),
            tooltip="Enable DC voltage scanning"
        )

        self.setattr_argument(
            "initial_voltage_set",
            NumberValue(default=0, min=0, max=100000, step=1, precision=0),
            tooltip="Initial voltage set index to start from (0-4)"
        )

        self.add_arg_from_param("frequency/397_cooling")
        self.add_arg_from_param("frequency/866_cooling")
        self.add_arg_from_param("frequency/854_dp")
        self.add_arg_from_param("frequency/397_far_detuned")
        
        self.add_arg_from_param("attenuation/397")
        self.add_arg_from_param("attenuation/866")
        self.add_arg_from_param("attenuation/854_dp")
        self.add_arg_from_param("attenuation/397_far_detuned")
        
        # Define the DC voltage sets similar to set_dc_manual.py
        self.channels = [i for i in range(32)]
        self.list_of_voltages = [{'DC21': -0.05575590291239997, 'DC20': -0.014093431620046146, 'DC19': 0.0702030341730586, 'DC18': 0.24945299896729783, 'DC17': -1.2464803791060566, 'DC16': 0.8093342592269501, 'DC15': -0.0634203178024998, 'DC14': -0.1983408785546452, 'DC13': -0.19382023373115473, 'DC12': -0.1293630087117353, 'DC10': -0.10972363761089274, 'DC9': -0.15012998464889557, 'DC8': -0.19854736717370147, 'DC7': -0.627766792983469, 'DC6': -1.0068557209744977, 'DC5': -0.44591547716473867, 'DC4': -0.5343352545427447, 'DC3': -0.3796528713476905, 'DC2': -0.25621843335818223, 'DC1': -0.17343828531698244, 'DC11': -0.24040373869576775},
{'DC21': -0.08363385436859996, 'DC20': -0.021140147430069218, 'DC19': 0.1053045512595879, 'DC18': 0.3741794984509468, 'DC17': -1.8697205686590848, 'DC16': 1.2140013888404253, 'DC15': -0.09513047670374972, 'DC14': -0.29751131783196777, 'DC13': -0.2907303505967321, 'DC12': -0.19404451306760295, 'DC10': -0.16458545641633912, 'DC9': -0.22519497697334337, 'DC8': -0.2978210507605522, 'DC7': -0.9416501894752036, 'DC6': -1.5102835814617466, 'DC5': -0.6688732157471081, 'DC4': -0.8015028818141172, 'DC3': -0.5694793070215358, 'DC2': -0.3843276500372733, 'DC1': -0.2601574279754737, 'DC11': -0.36060560804365166},
{'DC21': -0.11151180582479994, 'DC20': -0.028186863240092293, 'DC19': 0.1404060683461172, 'DC18': 0.49890599793459567, 'DC17': -2.492960758212113, 'DC16': 1.6186685184539003, 'DC15': -0.1268406356049996, 'DC14': -0.3966817571092904, 'DC13': -0.38764046746230946, 'DC12': -0.2587260174234706, 'DC10': -0.21944727522178548, 'DC9': -0.30025996929779114, 'DC8': -0.39709473434740294, 'DC7': -1.255533585966938, 'DC6': -2.0137114419489954, 'DC5': -0.8918309543294773, 'DC4': -1.0686705090854893, 'DC3': -0.759305742695381, 'DC2': -0.5124368667163645, 'DC1': -0.3468765706339649, 'DC11': -0.4808074773915355},
{'DC21': -0.13938975728099992, 'DC20': -0.035233579050115364, 'DC19': 0.17550758543264652, 'DC18': 0.6236324974182447, 'DC17': -3.1162009477651416, 'DC16': 2.0233356480673756, 'DC15': -0.15855079450624948, 'DC14': -0.495852196386613, 'DC13': -0.4845505843278868, 'DC12': -0.3234075217793383, 'DC10': -0.27430909402723186, 'DC9': -0.37532496162223894, 'DC8': -0.49636841793425374, 'DC7': -1.5694169824586726, 'DC6': -2.517139302436244, 'DC5': -1.114788692911847, 'DC4': -1.3358381363568619, 'DC3': -0.9491321783692263, 'DC2': -0.6405460833954556, 'DC1': -0.4335957132924561, 'DC11': -0.6010093467394194},
{'DC21': -0.16726770873719993, 'DC20': -0.042280294860138436, 'DC19': 0.2106091025191758, 'DC18': 0.7483589969018936, 'DC17': -3.7394411373181695, 'DC16': 2.4280027776808506, 'DC15': -0.19026095340749943, 'DC14': -0.5950226356639355, 'DC13': -0.5814607011934642, 'DC12': -0.3880890261352059, 'DC10': -0.32917091283267824, 'DC9': -0.45038995394668674, 'DC8': -0.5956421015211044, 'DC7': -1.8833003789504073, 'DC6': -3.020567162923493, 'DC5': -1.3377464314942162, 'DC4': -1.6030057636282344, 'DC3': -1.1389586140430716, 'DC2': -0.7686553000745466, 'DC1': -0.5203148559509474, 'DC11': -0.7212112160873033},
{'DC21': -0.1951456601933999, 'DC20': -0.049327010670161514, 'DC19': 0.24571061960570512, 'DC18': 0.8730854963855426, 'DC17': -4.362681326871198, 'DC16': 2.832669907294326, 'DC15': -0.22197111230874927, 'DC14': -0.6941930749412581, 'DC13': -0.6783708180590415, 'DC12': -0.4527705304910735, 'DC10': -0.3840327316381246, 'DC9': -0.5254549462711345, 'DC8': -0.6949157851079553, 'DC7': -2.1971837754421415, 'DC6': -3.523995023410741, 'DC5': -1.5607041700765856, 'DC4': -1.8701733908996068, 'DC3': -1.328785049716917, 'DC2': -0.8967645167536378, 'DC1': -0.6070339986094386, 'DC11': -0.8414130854351871},
{'DC21': -0.22302361164959988, 'DC20': -0.056373726480184586, 'DC19': 0.2808121366922344, 'DC18': 0.9978119958691913, 'DC17': -4.985921516424226, 'DC16': 3.2373370369078005, 'DC15': -0.2536812712099992, 'DC14': -0.7933635142185808, 'DC13': -0.7752809349246189, 'DC12': -0.5174520348469412, 'DC10': -0.43889455044357095, 'DC9': -0.6005199385955823, 'DC8': -0.7941894686948059, 'DC7': -2.511067171933876, 'DC6': -4.027422883897991, 'DC5': -1.7836619086589547, 'DC4': -2.1373410181709787, 'DC3': -1.518611485390762, 'DC2': -1.024873733432729, 'DC1': -0.6937531412679298, 'DC11': -0.961614954783071},
{'DC21': -0.2509015631057999, 'DC20': -0.06342044229020766, 'DC19': 0.31591365377876374, 'DC18': 1.1225384953528401, 'DC17': -5.609161705977255, 'DC16': 3.642004166521276, 'DC15': -0.2853914301112491, 'DC14': -0.8925339534959034, 'DC13': -0.8721910517901963, 'DC12': -0.5821335392028089, 'DC10': -0.49375636924901734, 'DC9': -0.6755849309200301, 'DC8': -0.8934631522816565, 'DC7': -2.824950568425611, 'DC6': -4.53085074438524, 'DC5': -2.0066196472413242, 'DC4': -2.404508645442351, 'DC3': -1.7084379210646072, 'DC2': -1.15298295011182, 'DC1': -0.780472283926421, 'DC11': -1.081816824130955},
{'DC21': -0.27877951456199984, 'DC20': -0.07046715810023073, 'DC19': 0.35101517086529305, 'DC18': 1.2472649948364893, 'DC17': -6.232401895530283, 'DC16': 4.046671296134751, 'DC15': -0.31710158901249896, 'DC14': -0.991704392773226, 'DC13': -0.9691011686557736, 'DC12': -0.6468150435586766, 'DC10': -0.5486181880544637, 'DC9': -0.7506499232444779, 'DC8': -0.9927368358685075, 'DC7': -3.138833964917345, 'DC6': -5.034278604872488, 'DC5': -2.229577385823694, 'DC4': -2.6716762727137238, 'DC3': -1.8982643567384525, 'DC2': -1.2810921667909112, 'DC1': -0.8671914265849122, 'DC11': -1.2020186934788388},
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

    def prepare(self):
        self.experiment_data.set_list_dataset("PMT_count", 1, broadcast=True)
        # Set initial voltage set based on user parameter
        self.current_voltage_set = self.initial_voltage_set
        # Ensure voltage set index is within valid range
        if self.current_voltage_set >= len(self.voltage_sets):
            self.current_voltage_set = 0
            print(f"Warning: Initial voltage set {self.initial_voltage_set} is out of range. Using 0 instead.")

    @kernel
    def run(self):
        # 
        self.setup_run()
        self.core.break_realtime()
        delay(3.0*ms)

        # Initialize zotino0
        self.zotino0.init()
        delay(10*ms)

        # Apply initial voltage set
        if self.scan_dc_voltages:
            self.zotino0.set_dac(self.voltage_sets[self.current_voltage_set], self.channels)
            delay(10*ms)

        self.dds_397_dp.set(self.frequency_397_cooling)
        self.dds_397_dp.set_att(self.attenuation_397)

        self.dds_397_far_detuned.set(self.frequency_397_far_detuned)
        self.dds_397_far_detuned.set_att(self.attenuation_397_far_detuned)
        
        self.dds_866_dp.set(self.frequency_866_cooling)
        self.dds_866_dp.set_att(self.attenuation_866)

        # self.dds_854_dp.set(self.frequency_854_dp)
        # self.dds_854_dp.set_att(self.attenuation_854_dp)

        self.dds_397_dp.sw.on()
        self.dds_866_dp.sw.on()
        self.dds_397_far_detuned.sw.on()
        # self.dds_854_dp.sw.on()

        if self.if_pulse:
            try:
                # Scan frequencies: original + 5 MHz, original - 5 MHz, original
                frequencies = [
                    self.frequency_397_far_detuned + 5*MHz,
                    self.frequency_397_far_detuned - 5*MHz,
                    self.frequency_397_far_detuned
                ]
                
                current_freq_index = 0
                current_freq_start_time = now_mu()
                freq_duration = 20*s  # 20 seconds for each frequency
                
                self.dds_397_far_detuned.set(frequencies[current_freq_index])
                
                # Add period counter for DC voltage scanning
                period_counter = 0
                
                while True:
                    # Check if it's time to switch frequency
                    elapsed_time = self.core.get_rtio_counter_mu() - current_freq_start_time
                    if elapsed_time >= self.core.seconds_to_mu(freq_duration):
                        # Move to next frequency
                        current_freq_index = (current_freq_index + 1) % len(frequencies)
                        # self.dds_397_far_detuned.set(frequencies[current_freq_index])
                        self.dds_397_far_detuned.set(170*MHz)
                        current_freq_start_time = now_mu()
                    
                    # Handle 866 blinking
                    self.dds_397_far_detuned.set(170*MHz)
                    self.dds_397_far_detuned.set_att(self.attenuation_397_far_detuned)
                    self.dds_866_dp.set_att(self.attenuation_866)
                    self.dds_866_dp.sw.on()
                    delay(self.on_secs)

                    self.dds_866_dp.set_att(self.attenuation_866 * 1.0)
                    delay(self.off_secs)

                    self.core.break_realtime()
                    self.dds_866_dp.sw.on()
                    self.dds_397_far_detuned.set(195*MHz)
                    self.dds_397_far_detuned.set_att(self.attenuation_397_far_detuned * 1.3)
                    num_pmt_pulses_on = self.ttl_pmt_input.count(
                        self.ttl_pmt_input.gate_rising(100.0*ms)
                    )
                    delay(1.0*ms)
                    self.dds_866_dp.sw.off()
                    num_pmt_pulses_off = self.ttl_pmt_input.count(
                        self.ttl_pmt_input.gate_rising(100.0*ms)
                    )
                    delay(1.0*ms)
                    num_pmt_pulses = 10 * (num_pmt_pulses_on - num_pmt_pulses_off) / 1.0
                    self.experiment_data.insert_nd_dataset("PMT_count", 0, num_pmt_pulses)
                    self.core.break_realtime()
                    self.dds_866_dp.sw.on()
                    delay(3.0*ms)
                    
                    # Increment period counter
                    period_counter += 1
                    
                    # Check if we should change DC voltage set (every 270 periods)
                    if self.scan_dc_voltages and period_counter >= 270:
                        period_counter = 0  # Reset counter
                        
                        # Move to next voltage set
                        self.current_voltage_set = (self.current_voltage_set + 1) % len(self.voltage_sets)
                        
                        # Apply new voltage set
                        self.zotino0.set_dac(self.voltage_sets[self.current_voltage_set], self.channels)
                        
                        # Add small delay to ensure voltages are set
                        delay(10*ms)
                        
                        print("Changed to voltage set", self.current_voltage_set)
                        print("Current voltages:", self.voltage_sets[self.current_voltage_set])
            
            except TerminationRequested:
                pass