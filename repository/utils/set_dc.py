from artiq.experiment import *

# from artiq.experiment import kernel, delay, s, dB, us, NumberValue, MHz, ms
import numpy as np

class Set_DC(EnvExperiment):

    # def __init__(self, a):
    #     super().__init__()
    def initialize(self):
        self.setattr_device("core")
        self.setattr_device("zotino0")

        self.multipoles = ['Ex','Ey','Ez','U1','U2','U3','U4','U5']
       
        self.multipole_matrix = np.array([[-7.23383059e-01,  1.86301820e+00, -2.85486169e+00,
        -1.23375234e-01,  2.75303363e-01,  3.11410190e-04,
        -8.02809599e-02, -1.82120644e-01],
       [-7.24922370e-01,  1.85474591e+00,  2.65610470e+00,
        -1.22592722e-01,  2.77594757e-01,  1.23409756e-04,
         1.40348748e-01, -1.82191007e-01],
       [-8.33047518e-01, -5.20202754e-01, -4.65450401e-02,
         6.19107261e-02,  1.81891333e-03,  1.92836245e-04,
        -3.47806928e-04,  1.20770997e-01],
       [-2.88305789e+00, -2.66826827e+00, -1.58106180e-01,
         3.14131836e-01,  5.44462727e-03,  6.93647002e-04,
         4.30205616e-03,  3.76810386e-01],
       [-5.48623987e+00, -4.43638865e+00, -2.86501687e-01,
         5.67244848e-01,  1.25671722e-02,  1.62018569e-03,
         6.33821377e-02, -4.03378458e-01],
       [-4.63533767e+00, -3.07242571e+00, -2.33013405e-01,
         4.26202415e-01,  2.02366318e-02,  1.52045503e-03,
         8.21531240e-02, -9.28370320e-01],
       [-1.38918608e+00, -6.51067046e-01, -6.28836920e-02,
         9.72111966e-02,  6.52871742e-03,  4.50186605e-04,
         2.43751883e-02, -2.76017711e-01],
       [ 6.36689807e-01, -5.55005828e-01, -5.05542420e-02,
         7.14767943e-02,  8.30435775e-04, -1.06077494e-04,
         6.45565677e-03, -1.74329400e-01],
       [ 1.96780969e+00, -2.76134832e+00, -1.68576690e-01,
         3.43222717e-01,  2.02934775e-03, -2.93133658e-04,
         2.69725621e-02, -6.01659275e-01],
       [ 4.24632519e+00, -3.95180032e+00,  1.04096446e-01,
         4.39684654e-01, -1.48771048e-02, -1.06930396e-03,
        -1.36038848e-02,  9.68650132e-02],
       [ 3.90376446e+00, -2.32187794e+00,  3.15665634e-01,
         2.22757860e-01, -1.41392874e-02, -1.19110482e-03,
        -4.62465554e-02,  7.35293893e-01],
       [ 1.19239509e+00, -4.20388609e-01,  1.02042393e-01,
         3.52576597e-02, -3.90789551e-03, -3.69220552e-04,
        -1.44785952e-02,  2.26658219e-01],
       [-2.56243664e+00,  7.15524334e-01, -3.73815935e-01,
        -1.84967192e-01, -4.29687757e-02,  4.80571128e-04,
         1.05831023e-01,  7.16151897e-01],
       [-1.30815979e+00,  1.05044726e+00,  5.26492741e-01,
        -2.68496778e-01, -7.87730813e-02,  4.08291781e-04,
        -1.71483888e-01, -3.34561506e-01],
       [ 1.24752730e+00,  3.53946256e-01, -5.48622122e-01,
        -8.46647819e-02, -3.62553459e-02, -2.30884707e-05,
         1.73788854e-01, -1.04927364e+00],
       [-7.99846105e-01,  2.77481922e+00, -1.20670011e-01,
        -1.87678421e-01, -1.38638207e-01, -3.09407019e-03,
         3.22429021e-02, -2.00920810e-01],
       [-7.83242038e-01,  2.77100282e+00, -1.22209641e-01,
        -1.86770630e-01, -1.38393855e-01,  3.51268091e-03,
         3.28108708e-02, -2.04283231e-01]])
       

    def build(self):
        self.initialize()
        self.setattr_argument(
            "Ex",
            NumberValue(default=5, min=-100, max=100, precision=8),
            tooltip='Ex'
        )
        self.setattr_argument(
            "Ey",
            NumberValue(default=5, min=-100, max=100, precision=8),
            tooltip='Ey'
        )
        self.setattr_argument(
            "Ez",
            NumberValue(default=5, min=-100, max=100, precision=8),
            tooltip='Ez'
        )
        self.setattr_argument(
            "U1",
            NumberValue(default=5, min=-100, max=100, precision=8),
            tooltip='U1'
        )
        self.setattr_argument(
            "U2",
            NumberValue(default=5, min=-100, max=100, precision=8),
            tooltip='U2'
        )
        self.setattr_argument(
            "U3",
            NumberValue(default=5, min=-100, max=100, precision=8),
            tooltip='U3'
        )
        self.setattr_argument(
            "U4",
            NumberValue(default=5, min=-100, max=100, precision=8),
            tooltip='U4'
        )
        self.setattr_argument(
            "U5",
            NumberValue(default=5, min=-100, max=1000, precision=8),
            tooltip='U5'
        )

        self.multipoles_values=np.array([self.Ex, self.Ey, self.Ez, self.U1, self.U2, self.U3, self.U4, self.U5])

        self.calc_voltages =  self.multipole_matrix @ self.multipoles_values
        self.dc_ids =  np.array([13, 12, 21, 20, 23, 11, 8, 4,
                           1, 14, 16, 15, 22, 9, 2, 19, 7])

        self.voltages = np.array([0.0] * 32)
        self.channels = [i for i in range(32)]   

        threashold = 10
        if max(self.voltages) > threashold or min(self.voltages) < -threashold or len(self.dc_ids) != len(self.calc_voltages):

          print('out of range, setting all to zero')
          print(self.calc_voltages)
          print(len(self.dc_ids), len(self.calc_voltages))
        else:
          for i, channel_num in enumerate(self.dc_ids):
             self.voltages[channel_num] = self.calc_voltages[i]
             print(f"Channel: {channel_num} set to { self.calc_voltages[i]}")
        

        



    @kernel
    def run(self):
        self.core.reset()
        self.core.break_realtime()
        self.zotino0.init()
        
        delay(10*ms)
        self.zotino0.set_dac(self.voltages, self.channels)

        print('All DACs successfully set.')