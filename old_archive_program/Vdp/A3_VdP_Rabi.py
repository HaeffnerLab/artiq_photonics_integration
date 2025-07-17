from acf.experiment import _ACFExperiment
from acf_sequences.sequences import sequences
from acf_config.arguments_definition import argument_manager
from acf.utils import get_config_dir
from artiq.experiment import *

from acf.function.fitting import *

import random

from artiq.coredevice.ad9910 import PHASE_MODE_ABSOLUTE, PHASE_MODE_CONTINUOUS, PHASE_MODE_TRACKING

class A3_VdP_Rabi(_ACFExperiment):

    def build(self): 
        
        self.setup(sequences)

        self.seq.doppler_cool.add_arguments_to_gui()
        self.seq.sideband_cool.add_arguments_to_gui()
        self.seq.repump_854.add_arguments_to_gui()
        self.seq.op_pump_sigma.add_arguments_to_gui()
        self.seq.op_pump.add_arguments_to_gui()
        self.seq.readout_397.add_arguments_to_gui()
        self.seq.ion_store.add_arguments_to_gui()

        self.setup_fit(fitting_func, 'Sin' ,-1)


        self.setattr_argument(
            "freq_729_dp",
            NumberValue(default=self.parameter_manager.get_param("qubit/Sm1_2_Dm5_2")-self.parameter_manager.get_param("qubit/vib_freq"), min=160*MHz, max=250*MHz, unit="MHz", precision=8),
            tooltip="729 double pass frequency for blue sideband",
            group='Rabi'
        )
        self.setattr_argument(
            "freq_729_sp",
            NumberValue(default=self.parameter_manager.get_param("frequency/729_sp"), min=20*MHz, max=250*MHz, unit="MHz", precision=8),
            tooltip="729 double pass frequency for resonance",
            group='Rabi'
        )
        self.setattr_argument(
            "att_729_dp",
            NumberValue(default=self.parameter_manager.get_param("attenuation/729_dp"), min=5*dB, max=30*dB, unit="dB", precision=6),
            tooltip="729 double pass frequency for resonance",
            group='Rabi'
        )
        self.setattr_argument(
            "att_729_sp",
            NumberValue(default=self.parameter_manager.get_param("attenuation/729_sp"), min=5*dB, max=30*dB, unit="dB", precision=6),
            tooltip="729 double pass frequency for resonance",
            group='Rabi'
        )


        #VdP Hamiltonian (2nd red sideband + 1st blue sideband) ######################################################################
        self.setattr_argument(
            "Vdp_freq_729_BSB_dp",
            NumberValue(default=self.parameter_manager.get_param("qubit/Sm1_2_Dm5_2")-self.parameter_manager.get_param("qubit/vib_freq"), min=180*MHz, max=250*MHz, unit="MHz", precision=8),
            tooltip="729 double pass frequency for resonance",
            group='VdP Hamiltonian'
        )
        self.setattr_argument(
            "Vdp_freq_729_2RSB_dp",
            NumberValue(default=self.parameter_manager.get_param("qubit/Sm1_2_Dm5_2")+2*self.parameter_manager.get_param("qubit/vib_freq"), min=180*MHz, max=250*MHz, unit="MHz", precision=8),
            tooltip="729 double pass frequency for resonance",
            group='VdP Hamiltonian'
        )
        self.setattr_argument(
            "Vdp_drive_att_2RSB",
            NumberValue(default=self.parameter_manager.get_param("attenuation/729_dp"), min=5*dB, max=30*dB, unit="dB", precision=6),
            tooltip="729 single pass amplitude",
            group='VdP Hamiltonian'
        )
        self.setattr_argument(
            "Vdp_drive_att_BSB",
            NumberValue(default=self.parameter_manager.get_param("attenuation/729_dp"), min=5*dB, max=30*dB, unit="dB", precision=6),
            tooltip="729 single pass amplitude",
            group='VdP Hamiltonian'
        )

        self.setattr_argument(
            "Vdp_freq_729_sp",
            NumberValue(default=self.parameter_manager.get_param("frequency/729_sp"), min=20*MHz, max=250*MHz, unit="MHz", precision=8),
            tooltip="729 double pass frequency for resonance",
            group='VdP Hamiltonian'
        )
        self.setattr_argument(
            "Vdp_att_729_sp",
            NumberValue(default=self.parameter_manager.get_param("attenuation/729_sp"), min=5*dB, max=30*dB, unit="dB", precision=6),
            tooltip="729 double pass frequency for resonance",
            group='VdP Hamiltonian'
        )

        self.setattr_argument(
            "Vdp_drive_freq_854",
            NumberValue(default=self.parameter_manager.get_param("frequency/854_dp"), min=40*MHz, max=250*MHz, unit="MHz", precision=8),
            tooltip="729 double pass frequency for resonance",
            group='VdP Hamiltonian'
        )
        self.setattr_argument(
            "Vdp_drive_freq_866",
            NumberValue(default=self.parameter_manager.get_param("frequency/866_cooling"), min=40*MHz, max=250*MHz, unit="MHz", precision=8),
            tooltip="729 double pass frequency for resonance",
            group='VdP Hamiltonian'
        )
        self.setattr_argument(
            "Vdp_drive_amp_854",
            NumberValue(default=1.0, min=0.5, max=1.0,  precision=6),
            tooltip="729 single pass amplitude",
            group='VdP Hamiltonian'
        )
        self.setattr_argument(
            "Vdp_drive_att_854",
            NumberValue(default=16*dB, min=5*dB, max=30*dB, unit="dB", precision=6),
            tooltip="729 single pass amplitude",
            group='VdP Hamiltonian'
        )
        self.setattr_argument(
            "Vdp_drive_att_866",
            NumberValue(default=self.parameter_manager.get_param("attenuation/866"), min=5*dB, max=30*dB, unit="dB", precision=6),
            tooltip="729 single pass amplitude",
            group='VdP Hamiltonian'
        )

        self.setattr_argument(
            "Vdp_drive_time_2RSB",
            NumberValue(default=self.parameter_manager.get_param("VdP1mode/Vdp_drive_time_2RSB"), min=0.*us, max=1000*us, unit='us'),
            tooltip="Drive time for RSB VdP Hamiltonian",
            group='VdP Hamiltonian'
        )
        self.setattr_argument(
            "Vdp_drive_time_BSB",
            NumberValue(default=self.parameter_manager.get_param("VdP1mode/Vdp_drive_time_BSB"), min=0.*us, max=1000*us, unit='us'),
            tooltip="Drive time for BSB VdP Hamiltonian",
            group='VdP Hamiltonian'
        )
        self.setattr_argument(
            "Repeat_Time",
            NumberValue(default=200, min=0, max=1000, precision=0,step=1),
            tooltip="Times for repeating drive pulses",
            group='VdP Hamiltonian'
        )


        #normal Rabi parameters  ######################################################################
        self.setattr_argument(
            "scan_rabi_t",
            Scannable(
                default=RangeScan(
                    start=0*us,
                    stop=100*us,
                    npoints=100
                ),
                global_min=0*us,
                global_max=10000*us,
                global_step=10*us,
                unit="us"
            ),
            tooltip="Scan parameter for sweeping the 729 double pass on time."
        )

        self.setattr_argument(
            "samples_per_time",
            NumberValue(default=50, precision=0, step=1),
            tooltip="Number of samples to take for each time",
        )
        self.setattr_argument("enable_thresholding", BooleanValue(True))
        self.setattr_argument(
            "threshold_pmt_count",
            NumberValue(default=self.parameter_manager.get_param("readout/threshold"), precision=8),
            tooltip="Threshold PMT counts",
        )


    def prepare(self):
        #set up fitting dataset
        self.fitting_func.setup(len(self.scan_rabi_t.sequence))

        # Create datasets
        num_samples = len(self.scan_rabi_t.sequence)
        self.experiment_data.set_nd_dataset("pmt_counts", [num_samples, self.samples_per_time], broadcast=True)
        self.experiment_data.set_list_dataset("pmt_counts_avg_thresholded",num_samples, broadcast=True)
        self.experiment_data.set_list_dataset("rabi_t", num_samples, broadcast=True)

        # Enable live plotting
        self.experiment_data.enable_experiment_monitor(
            y_data_name="pmt_counts_avg_thresholded",
            x_data_name="rabi_t",
            pen=False,
            fit_data_name='fit_signal'
        )

        self.rand_phase1= [ self.generate_random_float() for i in range(self.Repeat_Time)]
        self.rand_phase2= [ self.generate_random_float() for i in range(self.Repeat_Time)]
    
    @kernel
    def repump(self):
        delay(2*us)
        self.dds_854_dp.sw.on()
        self.dds_866_dp.sw.on()
        delay(5*us)
        self.dds_854_dp.sw.off()
        self.dds_866_dp.sw.off()
        delay(2*us)
    @kernel
    def Vdp_Evolve(self):

        #loss in the upper spin state
        self.dds_854_dp.set(self.Vdp_drive_freq_854, amplitude=self.Vdp_drive_amp_854)
        self.dds_866_dp.set(self.Vdp_drive_freq_866)
        self.dds_854_dp.set_att(self.Vdp_drive_att_854)
        self.dds_866_dp.set_att(self.Vdp_drive_att_866)


        self.dds_729_sp.set(self.Vdp_freq_729_sp)
        self.dds_729_sp.set_att(self.Vdp_att_729_sp)
        self.dds_729_sp.sw.on()

        delay(10*us)

        for i in range(self.Repeat_Time):
            #generate random phase
            # 2 order red sideband

            self.dds_729_dp.set(self.Vdp_freq_729_2RSB_dp, phase=self.rand_phase1[i])
            self.dds_729_dp.set_att(self.Vdp_drive_att_2RSB)
            self.dds_729_dp.sw.on()
            delay(self.Vdp_drive_time_2RSB)
            self.dds_729_dp.sw.off()
            # self.seq.rabi.run(
            #     self.Vdp_drive_time_2RSB,
            #     self.Vdp_freq_729_2RSB_dp,
            #     self.Vdp_freq_729_sp,
            #     self.Vdp_drive_att_2RSB,
            #     self.Vdp_att_729_sp,
            #     self.rand_phase1[i]
            # )
            self.repump()
            # self.seq.op_pump_sigma.run()

            self.dds_729_dp.set(self.Vdp_freq_729_BSB_dp, phase=self.rand_phase2[i])
            self.dds_729_dp.set_att(self.Vdp_drive_att_BSB)
            self.dds_729_dp.sw.on()
            delay(self.Vdp_drive_time_BSB)
            self.dds_729_dp.sw.off()
            
            # 1 order blue sideband
            # self.seq.rabi.run(
            #     self.Vdp_drive_time_BSB,
            #     self.Vdp_freq_729_BSB_dp,
            #     self.Vdp_freq_729_sp,
            #     self.Vdp_drive_att_2RSB,
            #     self.Vdp_att_729_sp,
            #     self.rand_phase2[i]
            # )
            
            delay(2*us)
            #self.seq.op_pump_sigma.run()
        
        self.dds_854_dp.sw.off()
        self.dds_866_dp.sw.off()
        self.dds_729_dp.sw.off()
        delay(5*us)


    def generate_random_float(self)->float:
        return random.random()


    @kernel
    def run(self):
        print("Running the script")
        self.setup_run()
        self.seq.ion_store.run()

        #set phase mode 
        delay(50*us)

        for time_i in range(len(self.scan_rabi_t.sequence)): 

            rabi_t = self.scan_rabi_t.sequence[time_i]
            total_thresh_count = 0
            total_pmt_counts = 0
            sample_num=0

            while sample_num<self.samples_per_time:

                #line trigger
                if self.seq.ac_trigger.run(self.core, self.core.seconds_to_mu(20*ms), self.core.seconds_to_mu(50*us) ) <0 : 
                    continue
                sample_num+=1
                delay(50*us)

                #854 repump
                self.seq.repump_854.run()
                #  Cool
                self.seq.doppler_cool.run()
                #sideband cooling
                self.seq.sideband_cool.run()
                #Vdp Evolution
                self.Vdp_Evolve()

                # Prepare the Spin State to |down>
                self.seq.repump_854.run()
                self.seq.op_pump_sigma.run()

                #run rabi flopping
                self.seq.rabi.run(rabi_t,
                                  self.freq_729_dp,
                                  self.freq_729_sp,
                                  self.att_729_dp,
                                  self.att_729_sp
                )

                #readout
                num_pmt_pulses=self.seq.readout_397.run()

                # 854 repump
                self.seq.repump_854.run()

                #protect ion
                self.seq.ion_store.run()
                delay(20*us)

                #Update dataset
                self.experiment_data.insert_nd_dataset("pmt_counts",
                                            [time_i, sample_num],
                                            num_pmt_pulses)
                
                if num_pmt_pulses < self.threshold_pmt_count:
                    total_thresh_count += 1

                total_pmt_counts += num_pmt_pulses

                delay(3*ms)
            
            self.experiment_data.append_list_dataset("rabi_t", rabi_t / us)

            if self.enable_thresholding:
                self.experiment_data.append_list_dataset("pmt_counts_avg_thresholded",
                                          float(total_thresh_count) / self.samples_per_time)
            else:
                self.experiment_data.append_list_dataset("pmt_counts_avg_thresholded",
                                          float(total_pmt_counts) / self.samples_per_time)
            delay(5*ms)

        self.seq.ion_store.run()
    
    def analyze(self):
        rabi_time=self.get_dataset("rabi_t")
        rabi_PMT=self.get_dataset('pmt_counts_avg_thresholded')
        self.fitting_func.fit(rabi_time, rabi_PMT)


    
    
