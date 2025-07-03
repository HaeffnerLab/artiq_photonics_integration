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
        # self.list_of_voltages = [{'DC21': 0.21, 'DC20': 0.2, 'DC19': 0.19, 'DC18': 0.18, 'DC17': 0.17, 'DC16': 0.16, 'DC15': 0.15, 'DC14': 0.14, 'DC13': 0.13, 'DC12': 0.12, 'DC10': 0.1, 'DC9': 0.09, 'DC8': 0.08, 'DC7': 0.07, 'DC6': 0.06, 'DC5': 0.05, 'DC4': 0.04, 'DC3': 0.03, 'DC2': 0.02, 'DC1': 0.01, 'DC11': 0.11}, {'DC21': 9.99, 'DC20': 9.0, 'DC19': 8.0, 'DC18': 7.0, 'DC17': 6.0, 'DC16': 5.0, 'DC15': 4.0, 'DC14': 3.0, 'DC13': 2.0, 'DC12': 1.0, 'DC10': -1.0, 'DC9': -2.0, 'DC8': -3.0, 'DC7': -4.0, 'DC6': -5.0, 'DC5': -6.0, 'DC4': -7.0, 'DC3': -8.0, 'DC2': -9.0, 'DC1': -9.99, 'DC11': 0.1}]

        self.list_of_voltages = [{'DC21': 3.760488316795766, 'DC20': -3.994448052046066, 'DC19': -3.119825369930695, 'DC18': 3.2381484713183513, 'DC17': 0.2296411747546803, 'DC16': -0.2898026806155171, 'DC15': -0.2932869962926207, 'DC14': -0.27433902299742546, 'DC13': -0.23755008428857657, 'DC12': -0.21139669389104207, 'DC10': -3.415518860332507, 'DC9': -3.1347184646789947, 'DC8': -4.052287691370577, 'DC7': -0.956288917205964, 'DC6': -0.6517356929222919, 'DC5': -0.4630038758117162, 'DC4': -0.36535142950188804, 'DC3': -0.3086459181968544, 'DC2': 0.3464826336326365, 'DC1': -0.23150897616483843, 'DC11': -0.8928438751056709}]

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
                    # self.frequency_397_far_detuned + 5*MHz,
                    # self.frequency_397_far_detuned - 5*MHz,
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
                        # self.dds_397_far_detuned.set(200*MHz)
                        current_freq_start_time = now_mu()
                    
                    # Handle 866 blinking
                    # self.dds_397_far_detuned.set(200*MHz)
                    self.dds_397_far_detuned.set_att(self.attenuation_397_far_detuned)
                    self.dds_866_dp.set_att(self.attenuation_866)
                    self.dds_866_dp.sw.on()
                    self.dds_397_dp.sw.on()
                    delay(self.on_secs)

                    self.dds_866_dp.set_att(self.attenuation_866 * 1.0) # If 1.0, then 100% attenuation and no blinking
                    delay(self.off_secs)

                    self.core.break_realtime()
                    self.dds_866_dp.sw.on()
                    self.dds_397_dp.sw.on()
                    # self.dds_397_far_detuned.set(205*MHz)
                    self.dds_397_far_detuned.set_att(self.attenuation_397_far_detuned * 1.0)
                    num_pmt_pulses_on = self.ttl_pmt_input.count(
                        self.ttl_pmt_input.gate_rising(100.0*ms)
                    )
                    delay(1.0*ms)
                    # self.dds_866_dp.sw.off()
                    self.dds_397_dp.sw.off()
                    num_pmt_pulses_off = self.ttl_pmt_input.count(
                        self.ttl_pmt_input.gate_rising(100.0*ms)
                    )
                    delay(1.0*ms)
                    num_pmt_pulses = 10 * (num_pmt_pulses_on - num_pmt_pulses_off) / 1.0
                    # self.experiment_data.insert_nd_dataset("PMT_count", 0, num_pmt_pulses)
                    self.core.break_realtime()
                    self.dds_866_dp.sw.on()
                    self.dds_397_dp.sw.on()
                    delay(3.0*ms)
                    
                    # Increment period counter
                    period_counter += 1
                    
                    # Check if we should change DC voltage set (every 10 periods)
                    if self.scan_dc_voltages and period_counter >= 10:
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