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
            tooltip="Alternate background and ion-plus-background PMT count rates"
        )

        self.setattr_argument(
            "on_secs",
            NumberValue(default=0.05*s, unit="s", min=1*ms, precision=8),
            tooltip="PMT integration time with 866 on (ion plus background)"
        )

        self.setattr_argument(
            "off_secs",
            NumberValue(default=0.01*s, unit="s", min=1*ms, max=20*ms, precision=8),
            tooltip="Total 866-off time, including settling and background counting (maximum 20 ms)"
        )

        self.setattr_argument(
            "background_settle_secs",
            NumberValue(default=100*us, unit="us", min=0*us, precision=1),
            tooltip="Wait after switching 866 off before counting; included in off_secs"
        )

        self.setattr_argument(
            "display_hold_secs",
            NumberValue(default=0.3*s, unit="s", min=0.1*s, precision=3),
            tooltip="Hold each displayed count rate while 866 is on and the ion cools"
        )

        self.setattr_argument(
            "initial_cooling_secs",
            NumberValue(default=100*ms, unit="ms", min=1*ms, precision=1),
            tooltip="Cooling before the first background measurement and after DC voltage changes"
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

        self.list_of_voltages = [

            #============================================================================================================================
           
            # (ex, ey, ez) = (0.0, 0.0, 0.0)
            #{'DC21': -0.10783251034786713, 'DC20': -0.15374048756523076, 'DC19': -0.17408036649703462, 'DC18': -0.32546600337180265, 'DC17': -0.05053830867419851, 'DC16': -0.761554685889015, 'DC15': -3.08399141556035, 'DC14': -0.3463994080438359, 'DC13': -0.11285254081038129, 'DC12': -0.29714907739834184, 'DC10': -0.162844355136414, 'DC9': -0.18643982099274498, 'DC8': -0.21520876531686606, 'DC7': -0.46844165028073403, 'DC6': -1.6087272467770144, 'DC5': -0.06774573202799183, 'DC4': -2.531792124615069, 'DC3': -0.03945315749397789, 'DC2': -0.30615428743467477, 'DC1': -0.5310721956639396, 'DC11': -0.43351624005600137} ,

            # (ex, ey, ez) = (0.0, 1.0, 0.0)
            #{'DC21': 0.05545342531144852, 'DC20': 0.08423353527390123, 'DC19': 0.09742721782273091, 'DC18': 0.32527158314941107, 'DC17': 1.1029148041974488, 'DC16': 0.7269094323962152, 'DC15': -2.5127655665915034, 'DC14': 0.4480241692169695, 'DC13': 1.5069003519104645, 'DC12': 0.7361239444461507, 'DC10': 0.06615780474033511, 'DC9': 0.08725662419905153, 'DC8': 0.090823211485735, 'DC7': 0.2053547467068802, 'DC6': 0.19549208181210442, 'DC5': 0.1567515190845486, 'DC4': -1.6030691652033005, 'DC3': 0.496165073348767, 'DC2': 0.540235308597375, 'DC1': 0.31999496145009454, 'DC11': -0.21239153556868645} ,

            # (ex, ey, ez) = (0.0, 2.0, 0.0)
            #{'DC21': 0.218739360970764, 'DC20': 0.322207558113033, 'DC19': 0.36893480214249674, 'DC18': 0.9760091696706253, 'DC17': 2.256367917069096, 'DC16': 2.2153735506814445, 'DC15': -1.9415397176226599, 'DC14': 1.2424477464777754, 'DC13': 3.1266532446313113, 'DC12': 1.7693969662906437, 'DC10': 0.2951599646170841, 'DC9': 0.36095306939084804, 'DC8': 0.396855188288336, 'DC7': 0.8791511436944944, 'DC6': 1.999711410401223, 'DC5': 0.38124877019708886, 'DC4': -0.6743462057915328, 'DC3': 1.031783304191513, 'DC2': 1.3866249046294254, 'DC1': 1.1710621185641288, 'DC11': 0.008733168918628338} ,
 
            # (ex, ey, ez) = (0.0, 2.5, 0.0)
            #{'DC21': 0.3003823288004218, 'DC20': 0.44119456953259917, 'DC19': 0.5046885943023793, 'DC18': 1.3013779629312312, 'DC17': 2.8330944735049197, 'DC16': 2.9596056098240595, 'DC15': -1.6559267931382375, 'DC14': 1.6396595351081769, 'DC13': 3.9365296909917333, 'DC12': 2.28603347721289, 'DC10': 0.4096610445554587, 'DC9': 0.4978012919867462, 'DC8': 0.5498711766896364, 'DC7': 1.2160493421883014, 'DC6': 2.901821074695782, 'DC5': 0.4934973957533601, 'DC4': -0.20998472608564764, 'DC3': 1.2995924196128852, 'DC2': 1.8098197026454501, 'DC1': 1.5965956971211455, 'DC11': 0.1192955211622856} ,

            # (ex, ey, ez) = (0.0, 3.0, 0.0)
            #{'DC21': 0.38202529663007956, 'DC20': 0.5601815809521654, 'DC19': 0.6404423864622621, 'DC18': 1.626746756191835, 'DC17': 3.409821029940743, 'DC16': 3.703837668966675, 'DC15': -1.3703138686538123, 'DC14': 2.0368713237385805, 'DC13': 4.746406137352156, 'DC12': 2.802669988135136, 'DC10': 0.5241621244938333, 'DC9': 0.6346495145826444, 'DC8': 0.7028871650909371, 'DC7': 1.5529475406821085, 'DC6': 3.803930738990341, 'DC5': 0.6057460213096297, 'DC4': 0.2543767536202369, 'DC3': 1.5674015350342563, 'DC2': 2.2330145006614748, 'DC1': 2.0221292756781626, 'DC11': 0.22985787340594258} ,

            # (ex, ey, ez) = (0.0, 3.5, 0.0)
            #{'DC21': 0.46366826445973786, 'DC20': 0.6791685923717312, 'DC19': 0.7761961786221457, 'DC18': 1.9521155494524451, 'DC17': 3.986547586376567, 'DC16': 4.448069728109291, 'DC15': -1.084700944169391, 'DC14': 2.434083112368981, 'DC13': 5.556282583712578, 'DC12': 3.319306499057382, 'DC10': 0.6386632044322078, 'DC9': 0.7714977371785428, 'DC8': 0.8559031534922377, 'DC7': 1.8898457391759163, 'DC6': 4.706040403284901, 'DC5': 0.7179946468659024, 'DC4': 0.7187382333261183, 'DC3': 1.8352106504556303, 'DC2': 2.6562092986774997, 'DC1': 2.44766285423518, 'DC11': 0.34042022564960067} ,

            # (ex, ey, ez) = (0.0, 4.0, 0.0)
            {'DC21': 0.545311232289395, 'DC20': 0.7981556037912974, 'DC19': 0.9119499707820277, 'DC18': 2.277484342713051, 'DC17': 4.563274142812391, 'DC16': 5.192301787251905, 'DC15': -0.7990880196849672, 'DC14': 2.831294900999387, 'DC13': 6.366159030073003, 'DC12': 3.8359430099796303, 'DC10': 0.7531642843705825, 'DC9': 0.9083459597744411, 'DC8': 1.0089191418935382, 'DC7': 2.2267439376697236, 'DC6': 5.60815006757946, 'DC5': 0.8302432724221688, 'DC4': 1.1830997130320065, 'DC3': 2.103019765877004, 'DC2': 3.079404096693526, 'DC1': 2.8731964327921977, 'DC11': 0.450982577893258} ,

            # (ex, ey, ez) = (0.0, 5.0, 0.0)
            #{'DC21': 0.7085971679487109, 'DC20': 1.0361296266304287, 'DC19': 1.1834575551017934, 'DC18': 2.928221929234262, 'DC17': 5.71672725568404, 'DC16': 6.680765905537134, 'DC15': -0.22786217071612333, 'DC14': 3.6257184782601954, 'DC13': 7.985911922793853, 'DC12': 4.8692160318241235, 'DC10': 0.9821664442473317, 'DC9': 1.182042404966238, 'DC8': 1.3149511186961393, 'DC7': 2.9005403346573377, 'DC6': 7.412369396168581, 'DC5': 1.0547405235347072, 'DC4': 2.1118226724437776, 'DC3': 2.6386379967197486, 'DC2': 3.9257936927255765, 'DC1': 3.7242635899062324, 'DC11': 0.672107282380573} ,

            # (ex, ey, ez) = (0.0, 6.0, 0.0)
            #{'DC21': 0.8718831036080271, 'DC20': 1.2741036494695615, 'DC19': 1.45496513942156, 'DC18': 3.578959515755481, 'DC17': 6.870180368555682, 'DC16': 8.169230023822363, 'DC15': 0.34336367825271985, 'DC14': 4.420142055520997, 'DC13': 9.605664815514691, 'DC12': 5.9024890536686145, 'DC10': 1.2111686041240803, 'DC9': 1.4557388501580337, 'DC8': 1.6209830954987399, 'DC7': 3.574336731644951, 'DC6': 9.216588724757697, 'DC5': 1.2792377746472512, 'DC4': 3.040545631855537, 'DC3': 3.1742562275624935, 'DC2': 4.772183288757624, 'DC1': 4.575330747020264, 'DC11': 0.8932319868678874} ,

            #============================================================================================================================

            # (zl_position, ex, ey, ez) = (670.0, 0.0, 3.0, 0.0)
            #{'DC21': 0.391917244877948, 'DC20': 0.5755110321955985, 'DC19': 0.6593624361628216, 'DC18': 1.6066771875999863, 'DC17': 3.3160818581986686, 'DC16': 3.4336512926801444, 'DC15': -1.5583928298704868, 'DC14': 2.5177530978135203, 'DC13': 4.955424927425117, 'DC12': 2.8801469609819597, 'DC10': 0.5218431797903689, 'DC9': 0.647997591014395, 'DC8': 0.7179499442661778, 'DC7': 1.606415066498892, 'DC6': 3.7332632166277624, 'DC5': 0.2658537690689077, 'DC4': 0.5579980363698103, 'DC3': 1.5021467721147244, 'DC2': 2.2576118385313104, 'DC1': 2.128531142152381, 'DC11': 0.24255160455307642} ,

            # (zl_position, ex, ey, ez) = (690.0, 0.0, 3.0, 0.0)
            #{'DC21': 0.3718607544903608, 'DC20': 0.5442648792064353, 'DC19': 0.6215485027791935, 'DC18': 1.579176362415228, 'DC17': 3.380572678185509, 'DC16': 3.8958938142757145, 'DC15': -0.864240293906429, 'DC14': 1.4210886616125857, 'DC13': 4.640534204388728, 'DC12': 2.6706591131006565, 'DC10': 0.50391482436463, 'DC9': 0.6221172225615319, 'DC8': 0.6902186245377717, 'DC7': 1.526594335318577, 'DC6': 3.7874235609024933, 'DC5': 1.0721806228958028, 'DC4': -0.02705395327306091, 'DC3': 1.726443778996539, 'DC2': 2.155607837172482, 'DC1': 2.000300691993642, 'DC11': 0.23746920786272996} ,

            #============================================================================================================================


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
                if value > 9.9*5:  #WARNING!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
                    remapped_voltages[key] = 9.9*5
                elif value < -9.9*5:
                    remapped_voltages[key] = -9.9*5
            
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
        if not 1*ms <= self.off_secs <= 20*ms:
            raise ValueError("off_secs must be between 1 ms and 20 ms, including settling.")
        if not 0 <= self.background_settle_secs < self.off_secs:
            raise ValueError("background_settle_secs must be nonnegative and shorter than off_secs.")
        if not self.on_secs >= 1*ms:
            raise ValueError("on_secs must be at least 1 ms.")
        if not self.display_hold_secs >= 0.1*s:
            raise ValueError("display_hold_secs must be at least 0.1 s.")
        if not self.initial_cooling_secs >= 1*ms:
            raise ValueError("initial_cooling_secs must be at least 1 ms.")

        # Normalize by the actual gate durations after conversion to RTIO units.
        self.on_gate_mu = self.core.seconds_to_mu(self.on_secs)
        self.off_duration_mu = self.core.seconds_to_mu(self.off_secs)
        self.background_settle_mu = self.core.seconds_to_mu(self.background_settle_secs)
        self.background_gate_mu = self.off_duration_mu - self.background_settle_mu
        if self.on_gate_mu <= 0 or self.background_gate_mu <= 0:
            raise ValueError("Both PMT gates must be at least one RTIO machine unit long.")
        self.on_gate_seconds = self.core.mu_to_seconds(self.on_gate_mu)
        self.background_gate_seconds = self.core.mu_to_seconds(self.background_gate_mu)

        # Convert voltages on the host; converting all 32 channels inside the
        # kernel can exhaust the RTIO slack before the first SPI write.
        self.voltage_sets_mu = [
            [self.zotino0.voltage_to_mu(voltage) for voltage in voltage_set]
            for voltage_set in self.voltage_sets
        ]

        self.experiment_data.set_list_dataset("PMT_count", 1, broadcast=True)
        # Set initial voltage set based on user parameter
        self.current_voltage_set = self.initial_voltage_set
        # Ensure voltage set index is within valid range
        if self.current_voltage_set >= len(self.voltage_sets):
            self.current_voltage_set = 0
            print(f"Warning: Initial voltage set {self.initial_voltage_set} is out of range. Using 0 instead.")

    @kernel
    def apply_voltage_set(self):
        # set_dac_mu schedules the SPI transfers before the current timestamp.
        # Add headroom after break_realtime for that rewind and kernel execution.
        self.core.break_realtime()
        delay(10*ms)
        self.zotino0.set_dac_mu(self.voltage_sets_mu[self.current_voltage_set], self.channels)
        delay(10*ms)  # Allow the DAC outputs to settle before continuing.

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
            self.apply_voltage_set()

        self.dds_397_dp.set(self.frequency_397_cooling)
        self.dds_397_dp.set_att(self.attenuation_397)

        self.dds_397_far_detuned.set(self.frequency_397_far_detuned)
        self.dds_397_far_detuned.set_att(self.attenuation_397_far_detuned)
        
        self.dds_866_dp.set(self.frequency_866_cooling)
        self.dds_866_dp.set_att(self.attenuation_866)

        self.dds_729_dp.set(self.frequency_729_dp)
        self.dds_729_dp.set_att(self.attenuation_729_dp)

        # Set 854 frequency and amplitud
        # 
        # 
        # 
        # 
        # 
        # 
        # 
        # 
        # 
        # 
        # 
        # 
        # 
        # 
        # 
        # 
        # 
        # 
        # 
        # 
        # e together to ensure a single IO_UPDATE
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
                # All beams except 866 retain their settings during both gates.
                # Display holds are cooling periods, not additional 866-off time.
                period_counter = 0
                delay(self.initial_cooling_secs)

                while True:
                    # Queue the entire short dark interval before any blocking
                    # read or host RPC, so neither can extend the 866-off time.
                    self.core.break_realtime()
                    self.dds_866_dp.sw.off()
                    delay_mu(self.background_settle_mu)
                    background_end = self.ttl_pmt_input.gate_rising_mu(self.background_gate_mu)
                    self.dds_866_dp.sw.on()
                    background_count = self.ttl_pmt_input.count(background_end)
                    background_cps = background_count / self.background_gate_seconds
                    self.experiment_data.insert_nd_dataset("PMT_count", 0, background_cps)

                    # Keep the background result visible while recooling, then
                    # acquire ion plus background with 866 still on.
                    self.core.break_realtime()
                    delay(self.display_hold_secs)
                    total_end = self.ttl_pmt_input.gate_rising_mu(self.on_gate_mu)
                    total_count = self.ttl_pmt_input.count(total_end)
                    total_cps = total_count / self.on_gate_seconds
                    self.experiment_data.insert_nd_dataset("PMT_count", 0, total_cps)

                    # Let the high result reach the applet before the next low
                    # update; 866 stays on throughout this display hold too.
                    self.core.break_realtime()
                    delay(self.display_hold_secs)
                    self.core.wait_until_mu(now_mu())
                    if self.scheduler.check_pause():
                        raise TerminationRequested

                    # Change voltages only after a complete background/total pair.
                    period_counter += 1
                    if self.scan_dc_voltages and period_counter >= 10:
                        period_counter = 0
                        self.current_voltage_set = (self.current_voltage_set + 1) % len(self.voltage_sets)

                        self.apply_voltage_set()
                        self.core.wait_until_mu(now_mu())
                        print("Changed to voltage set", self.current_voltage_set)
                        print("Current voltages:", self.voltage_sets[self.current_voltage_set])
                        self.core.break_realtime()
                        delay(self.initial_cooling_secs)

            except TerminationRequested:
                pass
            finally:
                self.core.break_realtime()
                self.dds_866_dp.sw.on()
                self.core.wait_until_mu(now_mu())
