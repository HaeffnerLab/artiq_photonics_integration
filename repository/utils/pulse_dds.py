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
            NumberValue(default=5*s, unit="s", min=0*s, precision=8),
            tooltip="Seconds on"
        )

        self.setattr_argument(
            "off_secs",
            NumberValue(default=1*s, unit="s", min=0*s, precision=8),
            tooltip="Seconds off"
        )

        self.setattr_argument(
            "scan_dc_voltages",
            BooleanValue(default=True),
            tooltip="Enable DC voltage scanning"
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
        self.list_of_voltages = [
            {'DC21': 1.0, 'DC20': -0.049327010670161514, 'DC19': 0.24571061960570512, 'DC18': 0.8730854963855426, 'DC17': -4.362681326871198, 'DC16': 2.832669907294326, 'DC15': -0.22197111230874927, 'DC14': -0.6941930749412581, 'DC13': -0.6783708180590415, 'DC12': -0.4527705304910735, 'DC10': -0.3840327316381246, 'DC9': -0.5254549462711345, 'DC8': -0.6949157851079553, 'DC7': -2.1971837754421415, 'DC6': -3.523995023410741, 'DC5': -1.5607041700765856, 'DC4': -1.8701733908996068, 'DC3': -1.328785049716917, 'DC2': -0.8967645167536378, 'DC1': -0.6070339986094386, 'DC11': -0.8414130854351871}, 
            {'DC21': 2.0, 'DC20': -0.06342044229020766, 'DC19': 0.31591365377876374, 'DC18': 1.1225384953528401, 'DC17': -5.609161705977255, 'DC16': 3.642004166521276, 'DC15': -0.2853914301112491, 'DC14': -0.8925339534959034, 'DC13': -0.8721910517901963, 'DC12': -0.5821335392028089, 'DC10': -0.49375636924901734, 'DC9': -0.6755849309200301, 'DC8': -0.8934631522816565, 'DC7': -2.824950568425611, 'DC6': -4.53085074438524, 'DC5': -2.0066196472413242, 'DC4': -2.404508645442351, 'DC3': -1.7084379210646072, 'DC2': -1.15298295011182, 'DC1': -0.780472283926421, 'DC11': -1.081816824130955}, 
            {'DC21': 3.0, 'DC20': -0.0775138739102538, 'DC19': 0.38611668795182236, 'DC18': 1.3719914943201381, 'DC17': -6.8556420850833115, 'DC16': 4.451338425748226, 'DC15': -0.3488117479137489, 'DC14': -1.0908748320505486, 'DC13': -1.066011285521351, 'DC12': -0.7114965479145442, 'DC10': -0.6034800068599101, 'DC9': -0.8257149155689256, 'DC8': -1.092010519455358, 'DC7': -3.4527173614090794, 'DC6': -5.5377064653597365, 'DC5': -2.452535124406063, 'DC4': -2.938843899985096, 'DC3': -2.088090792412298, 'DC2': -1.4092013834700023, 'DC1': -0.9539105692434033, 'DC11': -1.3222205628267227}
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
        self.current_voltage_set = 0

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
                        self.dds_397_far_detuned.set(175*MHz)
                        current_freq_start_time = now_mu()
                    
                    # Handle 866 blinking
                    self.dds_397_far_detuned.set(175*MHz)
                    self.dds_866_dp.set_att(self.attenuation_866)
                    self.dds_866_dp.sw.on()
                    delay(self.on_secs)

                    self.dds_866_dp.set_att(self.attenuation_866 * 1.0)
                    delay(self.off_secs)

                    self.core.break_realtime()
                    self.dds_866_dp.sw.on()
                    self.dds_397_far_detuned.set(205*MHz)
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
                    
                    # Check if we should change DC voltage set (every 10 periods)
                    if self.scan_dc_voltages and period_counter >= 30:
                        period_counter = 0  # Reset counter
                        
                        # Move to next voltage set
                        self.current_voltage_set = (self.current_voltage_set + 1) % len(self.voltage_sets)
                        
                        # Apply new voltage set
                        self.zotino0.set_dac(self.voltage_sets[self.current_voltage_set], self.channels)
                        
                        # Add small delay to ensure voltages are set
                        delay(10*ms)
                        
                        print("Changed to voltage set", self.current_voltage_set)
            
            except TerminationRequested:
                pass