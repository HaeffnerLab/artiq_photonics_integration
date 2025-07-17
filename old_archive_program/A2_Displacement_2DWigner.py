from acf.experiment import _ACFExperiment
from acf_sequences.sequences import sequences
from acf_config.arguments_definition import argument_manager

from artiq.experiment import *

from acf.function.fitting import *
from acf.utils import get_config_dir

'''

artificially create an displacement state after state preparation, and readout 2D wigner function

'''

class A2_Displace_Wigner_2D(_ACFExperiment):

    def build(self): 
        
        self.setup(sequences)

        self.seq.sideband_cool.add_arguments_to_gui()
        self.seq.doppler_cool.add_arguments_to_gui()
        self.seq.repump_854.add_arguments_to_gui()
        self.seq.readout_397.add_arguments_to_gui()
        self.seq.ion_store.add_arguments_to_gui()
    

        self.setattr_argument("enable_rot_pulse", BooleanValue(False), group='rotation pulse excitation')
        self.setattr_argument(
            "freq_729_dp_rot",
            NumberValue(default=self.parameter_manager.get_param("qubit/Sm1_2_Dm1_2"), min=200*MHz, max=250*MHz, unit="MHz", precision=8),
            tooltip="729 double pass frequency for resonance",
            group='rotation pulse excitation'
        )
        self.setattr_argument(
            "att_729_dp_rot",
            NumberValue(default=self.parameter_manager.get_param("attenuation/729_dp"), min=5*dB, max=30*dB, unit="dB", precision=8),
            tooltip="729 double pass amplitude for resonance",
            group='rotation pulse excitation'
        )
        self.setattr_argument(
            "freq_729_sp_rot",
            NumberValue(default=self.parameter_manager.get_param("frequency/729_sp"), min=200*MHz, max=250*MHz, unit="MHz", precision=8),
            tooltip="729 double pass frequency for resonance",
            group='rotation pulse excitation'
        )
        self.setattr_argument(
            "att_729_sp_rot",
            NumberValue(default=self.parameter_manager.get_param("attenuation/729_sp"), min=5*dB, max=30*dB, unit="dB", precision=8),
            tooltip="729 double pass amplitude for resonance",
            group='rotation pulse excitation'
        )
        self.setattr_argument(
            "rot_drive_time",
            NumberValue(default=0.1*us, min=0.*us, max=1000*us, unit='us', precision=8),
            tooltip="Drive time for pi excitation",
            group='rotation pulse excitation'
        )  
      

        # Motional State Readout (displacement operator) https://journals.aps.org/prl/pdf/10.1103/PhysRevLett.125.043602 

        # get the wigner function after trace out spin degrees of freedom  
        # displacement operation (may need to be a bit offseted due to stark shift)
        self.setattr_argument(
            "displace_freq_729_dp_resonance",
            NumberValue(default=self.parameter_manager.get_param("qubit/Sm1_2_Dm5_2"), min=200*MHz, max=250*MHz, unit="MHz", precision=6),
            tooltip="729 double pass frequency 1",
            group='Displacement Operation'
        )
        self.setattr_argument(
            "displace_freq_729_sp",
            NumberValue(default=self.parameter_manager.get_param("frequency/729_sp")-2*self.parameter_manager.get_param("qubit/vib_freq"), min=50*MHz, max=120*MHz, unit="MHz", precision=6),
            tooltip="729 single pass frequency 1",
            group='Displacement Operation'
        )
        self.setattr_argument(
            "displace_freq_729_sp_aux",
            NumberValue(default=self.parameter_manager.get_param("frequency/729_sp")+2*self.parameter_manager.get_param("qubit/vib_freq"), min=50*MHz, max=120*MHz, unit="MHz", precision=6),
            tooltip="729 single pass frequency 2",
            group='Displacement Operation'
        )
        # 
        self.setattr_argument(
            "displace_att_729_dp",
            NumberValue(default=self.parameter_manager.get_param("attenuation/729_dp"), min=5*dB, max=30*dB, unit="dB", precision=5),
            tooltip="729 douuble pass amplitude 1",
            group='Displacement Operation'
        )
        self.setattr_argument(
            "displace_att_729_sp",
            NumberValue(default=self.parameter_manager.get_param("attenuation/729_sp"), min=5*dB, max=30*dB, unit="dB", precision=5),
            tooltip="729 single pass amplitude 1",
            group='Displacement Operation'
        )
        self.setattr_argument(
            "displace_att_729_sp_aux",
            NumberValue(default=self.parameter_manager.get_param("attenuation/729_sp"), min=5*dB, max=30*dB, unit="dB", precision=5),
            tooltip="729 single pass amplitude 2",
            group='Displacement Operation'
        )

        # the scan parameter for the displacement operator
        self.setattr_argument(
            "beta_range",
            NumberValue(default=4, min=0.001, max=300,  precision=8),
            tooltip="729 single pass amplitude",
            group='beta grid'
        )
        self.setattr_argument(
            "num_beta",
            NumberValue(default=15, precision=0, step=1),
            tooltip="Number of samples to take for each time",
            group='beta grid'
        )
        self.setattr_argument(
            "Rabi_freq",
            NumberValue(default=0.08*MHz, precision=8, min=0.001*MHz, max=2*MHz, unit='MHz'),
            tooltip="blue sideband rabi frequency",
            group='beta grid'
        )

        # general sampling parameters
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
        
        # Create datasets
        num_freq_samples = self.num_beta*self.num_beta
        # self.experiment_data.set_nd_dataset("pmt_counts", [num_freq_samples, self.samples_per_time])
        self.experiment_data.set_list_dataset("pmt_counts_avg_thresholded", num_freq_samples, broadcast=True)
        self.experiment_data.set_list_dataset("beta_index", num_freq_samples, broadcast=True)

        # Enable live plotting
        self.experiment_data.enable_experiment_monitor(
            "pmt_counts_avg_thresholded",
            x_data_name="beta_index",
            pen=False
        )

        #beta sampling
        self.beta=np.linspace(-self.beta_range,self.beta_range,self.num_beta).reshape((self.num_beta,1))+1.0j*np.linspace(-self.beta_range,self.beta_range, self.num_beta).reshape((1,self.num_beta))

        np.savetxt(get_config_dir()/'../repository/Vdp/beta.txt', self.beta)
        print(self.beta)
        #from beta to corresponding time & phase
        self.beta_time=np.zeros(self.beta.shape[0]*self.beta.shape[1],dtype=float)
        self.beta_phase=np.zeros(self.beta.shape[0]*self.beta.shape[1],dtype=float)
        
        #compute the time & phase based on the parameters
        idx=0
        for i in range(self.beta.shape[0]):
            for j in range(self.beta.shape[1]):
                self.beta_time[idx]=float(np.abs(self.beta[i][j])*1.0/(self.Rabi_freq/MHz))*us
                self.beta_phase[idx]=(np.angle(self.beta[i][j])-np.pi/2)/(2*np.pi) #in unit of turns (2pi)
                self.beta_phase[idx]-=np.floor(self.beta_phase[idx])
                idx+=1
        np.savetxt(get_config_dir()/'../repository/Vdp/beta_time.txt', self.beta_time)
        np.savetxt(get_config_dir()/'../repository/Vdp/beta_phase.txt', self.beta_phase)  

    @kernel
    def displacement(self,drive_time, drive_phase:float):
        
        #set attenuation
        self.dds_729_dp.set_att(self.displace_att_729_dp)
        self.dds_729_sp.set_att(self.displace_att_729_sp)
        self.dds_729_sp_aux.set_att(self.displace_att_729_sp_aux)

        #set frequency
        self.dds_729_dp.set(self.displace_freq_729_dp_resonance)
        self.dds_729_sp.set(self.displace_freq_729_sp)
        self.dds_729_sp_aux.set(self.displace_freq_729_sp_aux, phase=drive_phase)

        #turn on the 729
        self.dds_729_dp.sw.on()
        self.dds_729_sp.sw.on()
        self.dds_729_sp_aux.sw.on()
        delay(drive_time)
        self.dds_729_dp.sw.off()

    @kernel
    def run(self):

        print("Running the script")
        self.setup_run()
        delay(10*us)
        self.seq.ion_store.run()

        delay(50*us)

        for i in range(len(self.beta_time)):

            total_thresh_count = 0
            total_pmt_counts = 0

            # counter for repeating 
            sample_num=0

            while sample_num<self.samples_per_time:

                #line trigger
                if self.seq.ac_trigger.run(self.core, self.core.seconds_to_mu(25*ms), self.core.seconds_to_mu(50*us) ) <0 : 
                    continue
                sample_num+=1
                delay(50*us)

                #854 repump
                self.seq.repump_854.run()
                #Cool
                self.seq.doppler_cool.run()
                #sideband cooling
                self.seq.sideband_cool.run()

                if self.enable_rot_pulse:
                    self.seq.rabi.run(self.rot_drive_time,
                                  self.freq_729_dp_rot,
                                  self.freq_729_sp_rot,
                                  self.att_729_dp_rot,
                                  self.att_729_sp_rot,
                                  phase = 0.0)


                # Drive to a displacement state in x direction --> |up>x|alpha>
                self.seq.displacement.run(float(1.0/(self.Rabi_freq/MHz))*us,
                     self.displace_att_729_dp, self.displace_att_729_sp, self.displace_att_729_sp_aux,
                     self.displace_freq_729_dp_resonance, self.displace_freq_729_sp, self.displace_freq_729_sp_aux,
                     drive_phase_sp = 0.0, drive_phase_sp_aux = 0.5
                )

                # Prepare the Spin State to |down>
                self.seq.repump_854.run()

                # Apply displacement operator
                self.seq.displacement.run(self.beta_time[i],
                     self.displace_att_729_dp, self.displace_att_729_sp, self.displace_att_729_sp_aux,
                     self.displace_freq_729_dp_resonance, self.displace_freq_729_sp, self.displace_freq_729_sp_aux,
                     drive_phase_sp = self.beta_phase[i], drive_phase_sp_aux = 0.0
                )


                # Readout
                num_pmt_pulses=self.seq.readout_397.run()

                self.seq.repump_854.run()
                self.seq.ion_store.run()
                delay(20*us)

                # Update dataset
                # self.experiment_data.insert_nd_dataset("pmt_counts",
                #                             [i, sample_num],
                #                             num_pmt_pulses)
                # Record avergae spin
                if num_pmt_pulses < self.threshold_pmt_count:
                    total_thresh_count += 1
                total_pmt_counts += num_pmt_pulses
                delay(1.5*ms)
            
            #
            self.experiment_data.append_list_dataset("beta_index", i)

            if self.enable_thresholding:
                self.experiment_data.append_list_dataset("pmt_counts_avg_thresholded",
                                          float(total_thresh_count) / self.samples_per_time)
            else:
                self.experiment_data.append_list_dataset("pmt_counts_avg_thresholded",
                                          float(total_pmt_counts) / self.samples_per_time)
            delay(6*ms)

        self.seq.ion_store.run()
        delay(5*us)
    
    def analyze(self):

        pmt_count = np.array(self.get_dataset('pmt_counts_avg_thresholded'))

        np.save(get_config_dir()/'../repository/Vdp/chi.npy',pmt_count)

        pmt_count = pmt_count.reshape((self.num_beta, self.num_beta))

        pmt_count = np.fft.fftshift(np.fft.fft2(pmt_count))

        np.save(get_config_dir()/'../repository/Vdp/wigner.npy',pmt_count)

        # Step 6: Plot and save the image using imshow
        # plt.imshow(np.abs(pmt_count), cmap='gray')
        # plt.colorbar()
        # plt.show()
        # # plt.title('Magnitude of 2D FFT with fftshift')
        # plt.savefig("./wigner.png")
        # # rabi_time=self.get_dataset("rabi_t")
        # rabi_PMT=self.get_dataset('pmt_counts_avg_thresholded')
        # self.fitting_func.fit(rabi_time, rabi_PMT)


    
    