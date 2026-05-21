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

        self.list_of_voltages = [

            #============================================================================================================================

            #zl_position = +500.001
            #ez = -0.0,
            #ex = -0.0,
            #-----------------------------

            #ey = 9,
            {'DC21': 1.9584786133587688, 'DC20': 2.363644129790802, 'DC19': 2.958042396297813, 'DC18': 5.673398861749578, 'DC17': 9.850247986183785, 'DC16': 7.634178994004041, 'DC15': 2.3152071423445943, 'DC14': 7.6368217636624385, 'DC13': 9.826918033400379, 'DC12': 10.707704099738457, 'DC10': 2.7583481715870635, 'DC9': 3.5004958566945445, 'DC8': 4.402919432010507, 'DC7': 7.776528788414657, 'DC6': 15.05302746582154, 'DC5': 17.49486335805619, 'DC4': 8.075785445517647, 'DC3': 0.7350729864980713, 'DC2': 19.95740556131294, 'DC11': 1.9484305957799113, 'DC1': 0.0},

            #ey = 10,
            {'DC21': 2.2094294447500222, 'DC20': 2.643005701781958, 'DC19': 3.3074977462423307, 'DC18': 6.334316788344943, 'DC17': 10.930993951337378, 'DC16': 8.333727802523022, 'DC15': 2.613063543189571, 'DC14': 9.013988874395174, 'DC13': 10.695051591968731, 'DC12': 11.822703216933526, 'DC10': 3.091777053744113, 'DC9': 3.922361770046384, 'DC8': 4.9348582882248735, 'DC7': 8.711469482419021, 'DC6': 16.84361060060146, 'DC5': 19.581091516886573, 'DC4': 9.19262284002199, 'DC3': 1.0932054555866133, 'DC2': 22.322276271979096, 'DC11': 2.225727700052846, 'DC1': 0.0},

            #ey = 11,
            {'DC21': 2.4603802761412705, 'DC20': 2.922367273773112, 'DC19': 3.656953096186846, 'DC18': 6.995234714940329, 'DC17': 12.01173991649097, 'DC16': 9.033276611042002, 'DC15': 2.910919944034537, 'DC14': 10.39115598512789, 'DC13': 11.5631851505371, 'DC12': 12.937702334128605, 'DC10': 3.425205935901161, 'DC9': 4.344227683398222, 'DC8': 5.466797144439238, 'DC7': 9.646410176423382, 'DC6': 18.63419373538136, 'DC5': 21.667319675716943, 'DC4': 10.30946023452632, 'DC3': 1.451337924675151, 'DC2': 24.687146982645245, 'DC11': 2.5030248043257814, 'DC1': 0.0},

            #ey = 12,
            {'DC21': 2.7113311075325246, 'DC20': 3.2017288457642663, 'DC19': 4.006408446131367, 'DC18': 7.65615264153573, 'DC17': 13.092485881644581, 'DC16': 9.732825419560998, 'DC15': 3.2087763448795177, 'DC14': 11.76832309586061, 'DC13': 12.431318709105483, 'DC12': 14.052701451323696, 'DC10': 3.7586348180582125, 'DC9': 4.766093596750062, 'DC8': 5.998736000653606, 'DC7': 10.581350870427752, 'DC6': 20.424776870161292, 'DC5': 23.753547834547337, 'DC4': 11.426297629030664, 'DC3': 1.8094703937636953, 'DC2': 27.052017693311413, 'DC11': 2.780321908598718, 'DC1': 0.0},

            #ey = 13,
            {'DC21': 2.962281938923772, 'DC20': 3.481090417755419, 'DC19': 4.355863796075883, 'DC18': 8.317070568131097, 'DC17': 14.17323184679818, 'DC16': 10.432374228079976, 'DC15': 3.5066327457244957, 'DC14': 13.145490206593328, 'DC13': 13.299452267673834, 'DC12': 15.167700568518763, 'DC10': 4.09206370021526, 'DC9': 5.187959510101898, 'DC8': 6.53067485686797, 'DC7': 11.516291564432107, 'DC6': 22.21536000494119, 'DC5': 25.839775993377703, 'DC4': 12.543135023535006, 'DC3': 2.1676028628522492, 'DC2': 29.416888403977552, 'DC11': 3.0576190128716543, 'DC1': 0.0},

            #ey = 14,
            {'DC21': 3.2132327703150225, 'DC20': 3.760451989746575, 'DC19': 4.705319146020398, 'DC18': 8.977988494726489, 'DC17': 15.253977811951765, 'DC16': 11.13192303659896, 'DC15': 3.8044891465694683, 'DC14': 14.522657317326056, 'DC13': 14.167585826242203, 'DC12': 16.28269968571384, 'DC10': 4.425492582372308, 'DC9': 5.609825423453736, 'DC8': 7.062613713082334, 'DC7': 12.451232258436468, 'DC6': 24.005943139721104, 'DC5': 27.926004152208073, 'DC4': 13.659972418039342, 'DC3': 2.5257353319407994, 'DC2': 31.781759114643705, 'DC11': 3.3349161171445902, 'DC1': 0.0},

            #ey = 15,
            {'DC21': 3.464183601706274, 'DC20': 4.0398135617377315, 'DC19': 5.054774495964917, 'DC18': 9.63890642132189, 'DC17': 16.33472377710537, 'DC16': 11.831471845117944, 'DC15': 4.102345547414439, 'DC14': 15.899824428058778, 'DC13': 15.035719384810578, 'DC12': 17.39769880290893, 'DC10': 4.75892146452936, 'DC9': 6.031691336805576, 'DC8': 7.5945525692967015, 'DC7': 13.386172952440836, 'DC6': 25.79652627450103, 'DC5': 30.012232311038456, 'DC4': 14.776809812543675, 'DC3': 2.883867801029328, 'DC2': 34.14662982530987, 'DC11': 3.6122132214175258, 'DC1': 0.0},

            #ey = 16,
            {'DC21': 3.7151344330975244, 'DC20': 4.319175133728887, 'DC19': 5.404229845909435, 'DC18': 10.299824347917248, 'DC17': 17.41546974225897, 'DC16': 12.531020653636931, 'DC15': 4.400201948259415, 'DC14': 17.276991538791513, 'DC13': 15.903852943378942, 'DC12': 18.512697920104006, 'DC10': 5.09235034668641, 'DC9': 6.4535572501574165, 'DC8': 8.126491425511068, 'DC7': 14.3211136464452, 'DC6': 27.587109409280945, 'DC5': 32.09846046986884, 'DC4': 15.893647207048026, 'DC3': 3.2420002701178934, 'DC2': 36.51150053597603, 'DC11': 3.8895103256904617, 'DC1': 0.0},

            #ey = 17,
            {'DC21': 3.966085264488775, 'DC20': 4.598536705720035, 'DC19': 5.753685195853946, 'DC18': 10.960742274512619, 'DC17': 18.49621570741255, 'DC16': 13.2305694621559, 'DC15': 4.698058349104372, 'DC14': 18.654158649524213, 'DC13': 16.77198650194731, 'DC12': 19.627697037299075, 'DC10': 5.425779228843453, 'DC9': 6.875423163509247, 'DC8': 8.658430281725426, 'DC7': 15.256054340449548, 'DC6': 29.377692544060825, 'DC5': 34.18468862869918, 'DC4': 17.01048460155234, 'DC3': 3.6001327392064244, 'DC2': 38.87637124664216, 'DC11': 4.166807429963391, 'DC1': 0.0},

            #ey = 18,
            {'DC21': 4.217036095880025, 'DC20': 4.877898277711189, 'DC19': 6.103140545798466, 'DC18': 11.621660201108007, 'DC17': 19.57696167256615, 'DC16': 13.93011827067488, 'DC15': 4.995914749949351, 'DC14': 20.031325760256944, 'DC13': 17.64012006051566, 'DC12': 20.742696154494148, 'DC10': 5.759208111000503, 'DC9': 7.2972890768610865, 'DC8': 9.190369137939793, 'DC7': 16.190995034453916, 'DC6': 31.16827567884075, 'DC5': 36.27091678752958, 'DC4': 18.127321996056676, 'DC3': 3.9582652082949523, 'DC2': 41.24124195730832, 'DC11': 4.444104534236329, 'DC1': 0.0},

            #ey = 19,
            {'DC21': 4.467986927271278, 'DC20': 5.1572598497023465, 'DC19': 6.452595895742988, 'DC18': 12.282578127703436, 'DC17': 20.657707637719767, 'DC16': 14.629667079193894, 'DC15': 5.293771150794347, 'DC14': 21.408492870989672, 'DC13': 18.508253619084055, 'DC12': 21.85769527168925, 'DC10': 6.092636993157557, 'DC9': 7.719154990212931, 'DC8': 9.722307994154164, 'DC7': 17.125935728458288, 'DC6': 32.958858813620694, 'DC5': 38.35714494635997, 'DC4': 19.24415939056104, 'DC3': 4.3163976773835175, 'DC2': 43.60611266797451, 'DC11': 4.721401638509276, 'DC1': 0.0},

            #ey = 20,
            {'DC21': 4.718937758662518, 'DC20': 5.436621421693499, 'DC19': 6.802051245687501, 'DC18': 12.94349605429875, 'DC17': 21.738453602873353, 'DC16': 15.329215887712856, 'DC15': 5.5916275516393, 'DC14': 22.785659981722382, 'DC13': 19.376387177652408, 'DC12': 22.972694388884307, 'DC10': 6.4260658753146025, 'DC9': 8.141020903564764, 'DC8': 10.254246850368522, 'DC7': 18.060876422462634, 'DC6': 34.74944194840057, 'DC5': 40.44337310519032, 'DC4': 20.360996785065367, 'DC3': 4.674530146472083, 'DC2': 45.970983378640625, 'DC11': 4.998698742782204, 'DC1': 0.0},

            #ey = 21,
            {'DC21': 4.969888590053779, 'DC20': 5.715982993684664, 'DC19': 7.1515065956320205, 'DC18': 13.604413980894195, 'DC17': 22.819199568026963, 'DC16': 16.028764696231846, 'DC15': 5.8894839524842855, 'DC14': 24.16282709245514, 'DC13': 20.244520736220778, 'DC12': 24.0876935060794, 'DC10': 6.759494757471658, 'DC9': 8.562886816916608, 'DC8': 10.786185706582899, 'DC7': 18.995817116467016, 'DC6': 36.54002508318053, 'DC5': 42.52960126402074, 'DC4': 21.477834179569726, 'DC3': 5.032662615560621, 'DC2': 48.335854089306814, 'DC11': 5.275995847055143, 'DC1': 0.0},

            #ey = 22,
            {'DC21': 27.491528225805798, 'DC20': 10.3044390779529, 'DC19': 10.287391752497884, 'DC18': 16.375385293997244, 'DC17': 24.974438326143385, 'DC16': 15.145574017647704, 'DC15': 2.5166475547780007, 'DC14': 25.425649115876247, 'DC13': 21.772019191155852, 'DC12': 26.243943475182252, 'DC10': 9.544215740693176, 'DC9': 11.094828676576173, 'DC8': 13.216396374707898, 'DC7': 21.255820304370896, 'DC6': 38.72502926128985, 'DC5': 44.67784000744156, 'DC4': 22.729206079320452, 'DC3': 4.634178506505634, 'DC2': 44.66138661613413, 'DC11': 5.241859602459542, 'DC1': 0.0},

            #ey = 23,
            {'DC21': 26.111755007866794, 'DC20': 14.151496646002798, 'DC19': 13.449182551403297, 'DC18': 19.25450882317086, 'DC17': 27.29747273082668, 'DC16': 16.62662895532109, 'DC15': 0.05255131005946628, 'DC14': 27.416265760303983, 'DC13': 21.641765247868996, 'DC12': 28.19292199582521, 'DC10': 12.135087419588158, 'DC9': 13.507114666742446, 'DC8': 15.568112589391612, 'DC7': 23.430723440514523, 'DC6': 40.79076961500155, 'DC5': 44.81671229793754, 'DC4': 24.208790533109212, 'DC3': 4.424340695151844, 'DC2': 44.77795064024967, 'DC11': 5.355393741969797, 'DC1': 0.0},

            #ey = 24,
            {'DC21': 37.73438545188269, 'DC20': 17.4978022334869, 'DC19': 16.274513449481592, 'DC18': 21.847715442952243, 'DC17': 29.50225125280615, 'DC16': 18.102869650366195, 'DC15': -3.0585322611743977, 'DC14': 29.23349433030893, 'DC13': 21.666311324063418, 'DC12': 30.305602013509954, 'DC10': 14.602507746737185, 'DC9': 15.82644902724307, 'DC8': 17.82927830944251, 'DC7': 25.515966287958086, 'DC6': 42.7389893127113, 'DC5': 44.96786252499975, 'DC4': 25.76486221117458, 'DC3': 3.855681151505415, 'DC2': 44.001805712328014, 'DC11': 5.399085628301219, 'DC1': 0.0},

            #ey = 25,
            {'DC21': 45.83167025513524, 'DC20': 21.883753413924953, 'DC19': 20.249106594256972, 'DC18': 25.468020325044083, 'DC17': 32.482270242805306, 'DC16': 16.80589308916531, 'DC15': -5.230295906490163, 'DC14': 30.435041175781627, 'DC13': 21.729228234639045, 'DC12': 33.67184981403402, 'DC10': 18.315377104355395, 'DC9': 19.35604188887698, 'DC8': 21.227741823946744, 'DC7': 28.420088508681257, 'DC6': 44.735425950688956, 'DC5': 45.21849329092416, 'DC4': 27.059522965790546, 'DC3': 3.486077010361577, 'DC2': 42.12377485709991, 'DC11': 5.403982985122507, 'DC1': 0.0},

            #ey = 26,
            {'DC21': 43.24601383083663, 'DC20': 26.285379648647183, 'DC19': 24.591529351026328, 'DC18': 29.259197131189314, 'DC17': 35.4136812807736, 'DC16': 17.297740172119386, 'DC15': -8.539212446713222, 'DC14': 32.57391498291841, 'DC13': 21.399743273388534, 'DC12': 37.22362749995458, 'DC10': 22.204916449544292, 'DC9': 23.00752632118451, 'DC8': 24.70900854402111, 'DC7': 31.255230702821212, 'DC6': 45.78615369630706, 'DC5': 45.51914957723607, 'DC4': 29.367673041283357, 'DC3': 2.7572868757876874, 'DC2': 40.626517442380525, 'DC11': 5.456574340492394, 'DC1': 0.0},

            #ey = 27,
            {'DC21': 41.028490922690615, 'DC20': 30.972740007695162, 'DC19': 29.358803755813028, 'DC18': 33.276973468109425, 'DC17': 38.37349542292533, 'DC16': 17.225958864337905, 'DC15': -11.201849167835706, 'DC14': 34.393532181631336, 'DC13': 21.21097844421558, 'DC12': 40.353416437531415, 'DC10': 26.751900233769245, 'DC9': 27.29623856554351, 'DC8': 28.77648580071526, 'DC7': 34.43553257885352, 'DC6': 46.24487293251776, 'DC5': 45.475469675686206, 'DC4': 31.708589373170483, 'DC3': 1.9517706253896354, 'DC2': 39.60887104916861, 'DC11': 5.513415901364637, 'DC1': 0.0},

            #ey = 28,
            {'DC21': 39.492241271261946, 'DC20': 35.332409205600754, 'DC19': 33.90179541166541, 'DC18': 37.023234416910114, 'DC17': 41.06478731252004, 'DC16': 18.091327521804697, 'DC15': -14.039004214762, 'DC14': 36.35025614861792, 'DC13': 21.045292260014865, 'DC12': 42.73801898776084, 'DC10': 31.321884872726837, 'DC9': 31.63601941391117, 'DC8': 32.87575638116578, 'DC7': 37.55996733001715, 'DC6': 46.752316293580634, 'DC5': 44.69042582923947, 'DC4': 34.3938849801148, 'DC3': 0.9164304544835029, 'DC2': 39.28733181598221, 'DC11': 5.584830503274725, 'DC1': 0.0},

            #ey = 29,
            {'DC21': 42.6926714275491, 'DC20': 38.80965510854168, 'DC19': 37.78888759307201, 'DC18': 40.08401232747315, 'DC17': 43.13458855253778, 'DC16': 19.10535232604509, 'DC15': -16.468442809714066, 'DC14': 38.14586593512736, 'DC13': 21.36936881697101, 'DC12': 44.47010408326527, 'DC10': 35.28957674906425, 'DC9': 35.421045327552456, 'DC8': 36.42580837523381, 'DC7': 40.21823936678604, 'DC6': 47.23046248665527, 'DC5': 44.312222981609224, 'DC4': 37.11228099760246, 'DC3': -0.12814353767749118, 'DC2': 39.40380302183561, 'DC11': 5.683766436548122, 'DC1': 0.0},

            #ey = 30,
            {'DC21': 46.14065905344094, 'DC20': 39.75167165261175, 'DC19': 39.32014712934759, 'DC18': 41.34031434821761, 'DC17': 44.27486532548633, 'DC16': 37.30477078142028, 'DC15': -30.457217124197612, 'DC14': 45.53350138636585, 'DC13': 17.67845803398572, 'DC12': 45.301889667206126, 'DC10': 35.638184119949244, 'DC9': 35.72799431912276, 'DC8': 36.70093510238664, 'DC7': 40.62165336589145, 'DC6': 47.275890804352, 'DC5': 43.721882410284785, 'DC4': 40.149699694824896, 'DC3': -1.9541409950264224, 'DC2': 39.33646333436683, 'DC11': 5.694829774945908, 'DC1': 0.0},

            #ey = 35.0,
            # Start to hit 50V from here on

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
            delay(1.0*ms)#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
            self.core.break_realtime() #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
            self.zotino0.set_dac(self.voltage_sets[self.current_voltage_set], self.channels)
            delay(1.0*ms)#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
            delay(10*ms)

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
                        delay(1.0*ms) #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
                        self.core.break_realtime() #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
                        self.zotino0.set_dac(self.voltage_sets[self.current_voltage_set], self.channels)
                        delay(1.0*ms)#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
                        
                        # Add small delay to ensure voltages are set
                        delay(10*ms)
                        
                        print("Changed to voltage set", self.current_voltage_set)
                        print("Current voltages:", self.voltage_sets[self.current_voltage_set])
            
            except TerminationRequested:
                pass