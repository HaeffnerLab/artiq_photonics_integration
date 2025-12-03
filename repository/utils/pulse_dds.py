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

        self.list_of_voltages = [
        #     {'DC21': -0.0064239906855638115, 'DC20': 0.21014630321464717, 'DC19': 0.5403641914839818, 'DC18': 3.472877587084455, 'DC17': -1.9622792820745931, 'DC16': -5.059465439735055, 'DC15': 3.450560523416619, 'DC14': 0.2801507626439699, 'DC13': -0.525566768339635, 'DC12': -0.5398095200104401, 'DC10': -0.23998435048871308, 'DC9': -0.2354760919104214, 'DC8': -0.2421024005960481, 'DC7': 0.44331830356634183, 'DC6': -2.9286214464824045, 'DC5': -2.875666470982899, 'DC4': -1.8186708798027746, 'DC3': -2.0115440810490286, 'DC2': -1.4718311950690361, 'DC1': -1.012460304349394, 'DC11': -0.7455620228739208},

        # {'DC21': 0.11418238744910736, 'DC20': 0.21155007851749216, 'DC19': 0.30610906109071767, 'DC18': 1.0097744478897426, 'DC17': 1.7177420481593535, 'DC16': -3.2782202073217848, 'DC15': 1.721179200897584, 'DC14': 1.4757159419717985, 'DC13': 0.6672020194863629, 'DC12': 0.37117252256100575, 'DC10': 0.11842764701756668, 'DC9': 0.19161864386777325, 'DC8': 0.24658224634540393, 'DC7': 0.6977033219045669, 'DC6': 0.45455692951985527, 'DC5': -2.2003351921222607, 'DC4': 0.47537417321457054, 'DC3': 0.7136383780400236, 'DC2': 0.4214666505643684, 'DC1': 0.2680260856745178, 'DC11': -0.21864247447727278},
        
        # {'DC21': 0.0404191484027404, 'DC20': 0.08374683671677824, 'DC19': 0.13464142648602057, 'DC18': 0.5203078549810288, 'DC17': 2.8804598759615834, 'DC16': -2.5270522406181812, 'DC15': -1.7155007143731287, 'DC14': 2.948474675258651, 'DC13': 1.5703696055461966, 'DC12': 0.8057533840652229, 'DC10': 0.019920249337300827, 'DC9': 0.025242354088348462, 'DC8': 0.02558262286284399, 'DC7': 0.11443286506297329, 'DC6': 0.5806900806854358, 'DC5': -1.7313047634164036, 'DC4': -1.5449926884724987, 'DC3': 0.8812894156532418, 'DC2': 0.7150400496480649, 'DC1': 0.4582354449018754, 'DC11': -0.3053146386084778},
        
        # {'DC21': 0.08279405523957592, 'DC20': 0.14743453549648433, 'DC19': 0.19739336393733184, 'DC18': 0.5590622458046118, 'DC17': 2.1045690063035236, 'DC16': 0.19675754871276957, 'DC15': -3.164945157486676, 'DC14': 2.2828587108915026, 'DC13': 1.460909661518466, 'DC12': 0.7317061206668081, 'DC10': 0.08691966611132357, 'DC9': 0.1268113535180908, 'DC8': 0.15407863457544582, 'DC7': 0.3332871831531816, 'DC6': 1.005886862797341, 'DC5': -0.5796256876303845, 'DC4': -2.088355631417253, 'DC3': 0.5551746302279933, 'DC2': 0.6959437209647512, 'DC11': -0.26365233213793193, 'DC1': 0.0},
        
        # {'DC21': 0.025239709167228747, 'DC20': 0.051287137512212054, 'DC19': 0.08123741340196473, 'DC18': 0.21372498837561987, 'DC17': 1.1147532456423415, 'DC16': 2.609693324388897, 'DC15': -2.973503574199358, 'DC14': -0.9126490996727966, 'DC13': 3.051179430622695, 'DC12': 1.772607981674747, 'DC10': 0.04484612158269377, 'DC9': 0.0488355986865434, 'DC8': 0.05310316274362578, 'DC7': 0.06595782245492154, 'DC6': 0.3587880378234243, 'DC5': 0.6033063275460029, 'DC4': -2.0239821042449555, 'DC3': -1.1537500136968957, 'DC2': 1.4646572949369356, 'DC11': -0.29727125475593963, 'DC1': 0.0},
        
        {'DC21': 0.0838914567331214, 'DC20': 0.13275020011783678, 'DC19': 0.18678297950779668, 'DC18': 0.4615665851443141, 'DC17': 1.5300975821043605, 'DC16': 2.4913860331756905, 'DC15': -1.1364975555558197, 'DC14': -2.996254141880863, 'DC13': 2.963630518686353, 'DC12': 1.5647954496502354, 'DC10': 0.08571107615141287, 'DC9': 0.11779693645910014, 'DC8': 0.14577761682795978, 'DC7': 0.32387167207332834, 'DC6': 0.853802313570751, 'DC5': 0.7980833977222581, 'DC4': -1.3655837800539865, 'DC3': -1.9852041796951714, 'DC2': 0.7950285170805369, 'DC11': -0.31627254324022686, 'DC1': 0.0}]

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