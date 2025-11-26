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
            NumberValue(default=0.02*s, unit="s", min=0*s, precision=8),
            tooltip="Seconds on"
        )

        self.setattr_argument(
            "off_secs",
            NumberValue(default=0.02*s, unit="s", min=0*s, precision=8),
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
        self.add_arg_from_param("frequency/729_dp")
        
        self.add_arg_from_param("attenuation/397")
        self.add_arg_from_param("attenuation/866")
        self.add_arg_from_param("attenuation/854_dp")
        self.add_arg_from_param("attenuation/397_far_detuned")
        self.add_arg_from_param("attenuation/729_dp")
        
        # Allow manual control of 854 amplitude from ARTIQ dashboard (0.0 - 1.0)
        self.setattr_argument(
            "amplitude_854_dp",
            NumberValue(default=1.0, min=0.0, max=1.0, step=0.01),
            tooltip="Amplitude (0..1) for 854 DDS"
        )
        
        # Define the DC voltage sets similar to set_dc_manual.py
        self.channels = [i for i in range(32)]
        # self.list_of_voltages = [{'DC21': 0.21, 'DC20': 0.2, 'DC19': 0.19, 'DC18': 0.18, 'DC17': 0.17, 'DC16': 0.16, 'DC15': 0.15, 'DC14': 0.14, 'DC13': 0.13, 'DC12': 0.12, 'DC10': 0.1, 'DC9': 0.09, 'DC8': 0.08, 'DC7': 0.07, 'DC6': 0.06, 'DC5': 0.05, 'DC4': 0.04, 'DC3': 0.03, 'DC2': 0.02, 'DC1': 0.01, 'DC11': 0.11}, {'DC21': 9.99, 'DC20': 9.0, 'DC19': 8.0, 'DC18': 7.0, 'DC17': 6.0, 'DC16': 5.0, 'DC15': 4.0, 'DC14': 3.0, 'DC13': 2.0, 'DC12': 1.0, 'DC10': -1.0, 'DC9': -2.0, 'DC8': -3.0, 'DC7': -4.0, 'DC6': -5.0, 'DC5': -6.0, 'DC4': -7.0, 'DC3': -8.0, 'DC2': -9.0, 'DC1': -9.99, 'DC11': 0.1}]

        # self.list_of_voltages = [{'DC21': -0.5295629329142343, 'DC20': 1.143511249386009, 'DC19': -4.657589320169754, 'DC18': 1.084413000443012, 'DC17': -0.23835590013477692, 'DC16': -0.3975371068097732, 'DC15': -0.33957177605394506, 'DC14': -0.2872489091093875, 'DC13': -0.23420526857365886, 'DC12': -0.19574361762982595, 'DC10': -1.0820037661808874, 'DC9': -1.2813780053132249, 'DC8': -2.6555810834930442, 'DC7': -1.3071904427334418, 'DC6': -0.7678220571974826, 'DC5': -0.46211685669974367, 'DC4': -0.33388291767725947, 'DC3': -0.2518830675784012, 'DC2': -0.19279327485248154, 'DC1': -0.15249005914115782, 'DC11': -0.5346219132194117}]

        # self.list_of_voltages = [{'DC21': -0.6603610514394922, 'DC20': 3.7858266682355985, 'DC19': -5.04094216599675, 'DC18': -2.839830777977838, 'DC17': 4.62442366847759, 'DC16': 0.2570413228338185, 'DC15': -0.1133005318443239, 'DC14': -0.2003156413053016, 'DC13': -0.2156902076276706, 'DC12': -0.20703367925479793, 'DC10': -2.162924013358455, 'DC9': -3.163362503672918, 'DC8': -2.6221621780686775, 'DC7': -3.3065876041274906, 'DC6': -0.7998018646479924, 'DC5': -0.7827564201113086, 'DC4': -0.4995445343537429, 'DC3': -0.4593448334422925, 'DC2': -0.3164602530898525, 'DC1': -0.2500205681281304, 'DC11': -0.8220978330076305}]

        # self.list_of_voltages = [{'DC21': 0.12718469454428813, 'DC20': 3.439853967471257, 'DC19': -3.6402581025534277, 'DC18': -3.7166523980855413, 'DC17': 4.852153969447675, 'DC16': -0.14913026101592308, 'DC15': -0.6724215824451155, 'DC14': -0.38235534793950243, 'DC13': -0.35777420082836636, 'DC12': -0.3113434633727601, 'DC10': -1.1266803203065043, 'DC9': -1.682111631372993, 'DC8': -3.4740523230696505, 'DC7': -3.025011573972312, 'DC6': -2.6195211293835037, 'DC5': -1.4570743050708157, 'DC4': -1.0072790731272554, 'DC3': -0.7112138599342495, 'DC2': -0.51236159390516, 'DC1': -0.3802935497698644, 'DC11': -0.8454585763078156}]

        # self.list_of_voltages = [{'DC21': 3.1101114746684178, 'DC20': 2.3932462841161986, 'DC19': -1.2445248600766055, 'DC18': -0.9560682670419285, 'DC17': 7.527801325423099, 'DC16': 3.688403124321279, 'DC15': 2.616799500985873, 'DC14': 2.032507152568948, 'DC13': 1.5682917005079695, 'DC12': 1.2564238284176548, 'DC10': 4.0575043906435235, 'DC9': 3.8512204594448787, 'DC8': -3.008202030404183, 'DC5': 4.264809075770414, 'DC4': 2.810558008902429, 'DC3': 1.978290105957399, 'DC2': 1.4339031328681684, 'DC1': 1.1616305047466615, 'DC11': -0.1436866095486225, 'DC7': 0.0, 'DC6': 0.0}]

        # self.list_of_voltages = [{'DC21': -9.99, 'DC20': -9.0, 'DC19': -8.0, 'DC18': -7.0, 'DC17': -6.0, 'DC16': -5.0, 'DC15': -4.0, 'DC14': -3.0, 'DC13': -2.0, 'DC12': -1.0, 'DC10': +1.0, 'DC9': +2.0, 'DC8': +3.0, 'DC7': +4.0, 'DC6': +5.0, 'DC5': +6.0, 'DC4': +7.0, 'DC3': +8.0, 'DC2': +9.0, 'DC1': +9.99, 'DC11': +0.75}]

        self.list_of_voltages = [{'DC21': 0.6946564307382606, 'DC20': -3.955498506073728, 'DC19': 1.9112926435137751, 'DC18': 0.5256568218226814, 'DC17': -0.4531635053918349, 'DC16': -0.411871096028153, 'DC15': -0.35032538910415106, 'DC14': -0.2989103806062433, 'DC13': -0.24537412694919017, 'DC12': -0.21058532109324304, 'DC10': -2.423399850310038, 'DC9': -3.102450771582208, 'DC8': -2.297703314696033, 'DC7': -1.3056262357017618, 'DC6': -0.6787091406847442, 'DC5': -0.3972285627623062, 'DC4': -0.30188326769018303, 'DC3': -0.2337446969633486, 'DC2': -0.1845789690862304, 'DC1': -0.15337039692616927, 'DC11': -0.7828929131001141}]

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
        delay(3.0*ms)
        self.core.break_realtime()
        delay(3.0*ms)
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

        self.dds_729_dp.set(self.frequency_729_dp)
        self.dds_729_dp.set_att(self.attenuation_729_dp)

        # Set 854 frequency and amplitude together to ensure a single IO_UPDATE
        self.dds_854_dp.set(self.frequency_854_dp, amplitude=self.amplitude_854_dp)
        self.dds_854_dp.set_att(self.attenuation_854_dp)

        # self.dds_854_dp.set(self.frequency_854_dp)
        # self.dds_854_dp.set_att(self.attenuation_854_dp)

        self.dds_397_dp.sw.on()
        self.dds_866_dp.sw.on()
        self.dds_397_far_detuned.sw.on()
        self.dds_729_dp.sw.on()
        self.dds_854_dp.sw.on()

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
                save_on_cycle = 1
                
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
                    self.dds_854_dp.set_att(self.attenuation_854_dp)
                    self.dds_866_dp.sw.on()
                    self.dds_397_dp.sw.on()
                    delay(self.on_secs)

                    self.dds_866_dp.set_att(self.attenuation_866 * 1.0) # If 1.0, then 100% attenuation and no blinking
                    self.dds_854_dp.set_att(self.attenuation_854_dp * 1.0)
                    delay(self.off_secs)

                    self.core.break_realtime()
                    self.dds_866_dp.sw.on()
                    self.dds_397_dp.sw.on()
                    # self.dds_397_far_detuned.set(205*MHz)
                    self.dds_397_far_detuned.set_att(self.attenuation_397_far_detuned * 1.0)
                    self.dds_854_dp.set_att(self.attenuation_854_dp * 1.0)
                    num_pmt_pulses_on = self.ttl_pmt_input.count(
                        self.ttl_pmt_input.gate_rising(50.0*ms)
                    )
                    delay(1.0*ms)
                    # self.dds_866_dp.sw.off()
                    # self.dds_397_dp.sw.off()
                    # self.dds_854_dp.sw.off()
                    # self.dds_729_dp.sw.off()
                    num_pmt_pulses_off = self.ttl_pmt_input.count(
                        self.ttl_pmt_input.gate_rising(50.0*ms)
                    )
                    delay(1.0*ms)
                    if save_on_cycle == 1:
                        num_pmt_pulses = 20 * (num_pmt_pulses_on) / 1.0
                    else:   
                        num_pmt_pulses = 20  * (num_pmt_pulses_off) / 1.0
                    self.experiment_data.insert_nd_dataset("PMT_count", 0, num_pmt_pulses)
                    save_on_cycle = 1 - save_on_cycle
                    self.core.break_realtime()
                    self.dds_866_dp.sw.on()
                    self.dds_397_dp.sw.on()
                    self.dds_854_dp.sw.on()
                    self.dds_729_dp.sw.on()
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