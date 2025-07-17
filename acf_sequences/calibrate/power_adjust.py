from acf.sequence import Sequence

from artiq.experiment import kernel, delay, s, dB, us, NumberValue, MHz, ms
from numpy import int32, int64
import numpy as np
import random

class Adjust_729_Power(Sequence):

    def __init__(self):
        super().__init__()

    def build(self):
        super().build()
        #self.exp.setattr_device("sampler0")      

        self.setattr_argument(
            "cal_freq_729_dp",
            NumberValue(default=self.parameter_manager.get_param("qubit/Sm1_2_Dm1_2"), min=40*MHz, max=300*MHz, unit="MHz", precision=8),
            tooltip="729 double pass frequency",
            group="Adjust_729_Power"
        )

        self.setattr_argument(
            "cal_att_729_dp",
            NumberValue(default=15*dB, min=8*dB, max=31*dB, unit="dB", precision=8),
            tooltip="729 double pass attenuation",
            group="Adjust_729_Power"
        )

        self.setattr_argument(
            "cal_freq_729_sp",
            NumberValue(default=self.parameter_manager.get_param("frequency/729_sp"), min=40*MHz, max=160*MHz, unit="MHz", precision=8),
            tooltip="729 double pass frequency",
            group="Adjust_729_Power"
        )
        self.setattr_argument(
            "cal_att_729_sp",
            NumberValue(default=13*dB, min=8*dB, max=31*dB, unit="dB", precision=8),
            tooltip="729 double pass attenuation",
            group="Adjust_729_Power"
        )

        self.setattr_argument(
            "cal_att_range",
            NumberValue(default=0.5*dB, min=0*dB, max=31*dB, unit="dB", precision=8),
            tooltip="729 double pass attenuation",
            group="Adjust_729_Power"
        )

        self.setattr_argument(
            "cal_amp_step",
            NumberValue(default=0.0005, min=0, max=31,  precision=8),
            tooltip="729 double pass attenuation",
            group="Adjust_729_Power"
        )

        self.setattr_argument(
            "cal_att_num_samples_per_point",
            NumberValue(default=50, min=5, max=500,  step=1, precision=0),
            tooltip="729 double pass attenuation",
            group="Adjust_729_Power"
        )
        self.n_channels = 8
    def prepare(self):
        pass
    
    @kernel
    def init_sampler(self):
        self.sampler.init()   
        self.n_channels = 8                                                                                          
        for i in range(self.n_channels):                  
            self.sampler.set_gain_mu(7-i, 0)   
        self.core.break_realtime()  

    @kernel 
    def get_volt(self, amp_729_dp)->float:
        #print("get_volt_at:", att_729)
        self.core.break_realtime()
        self.dds_729_dp.set_att(self.cal_att_729_dp)
        self.dds_729_dp.set(self.cal_freq_729_dp, amplitude=amp_729_dp)
        delay(10*us)
        self.dds_729_sp.set(self.cal_freq_729_sp)
        self.dds_729_sp.set_att(self.cal_att_729_sp)
        delay(10*us)
        self.ttl_rf_switch_AWG_729SP.off()
        self.ttl_rf_switch_DDS_729SP.on()
        
        delay(10*us)
        self.core.break_realtime() 
        

        self.dds_729_sp.sw.on()
        self.dds_729_sp_aux.sw.off()
        self.dds_729_dp.sw.off()
        delay(1*s)
        
        total_pmt_counts = 0.0
        for _ in range(200+self.cal_att_num_samples_per_point):
            smp = [0.0]*self.n_channels
             
            self.dds_729_dp.sw.on()
            delay(3*ms)                 
            if _>=200:
                self.sampler.sample(smp)     
                delay(150*us)
                total_pmt_counts += smp[0]
            delay(1*ms)       
            self.dds_729_dp.sw.off()
            delay(3*ms) 
        
        self.dds_729_sp.sw.off()
        self.dds_729_sp_aux.sw.off()
        self.dds_729_dp.sw.off()
        #print("get_volt:", total_pmt_counts/(1.0*self.cal_att_num_samples_per_point))
        self.core.break_realtime()  

            

        return total_pmt_counts/(1.0*self.cal_att_num_samples_per_point)

    @kernel
    def find_root(self, amp_now, target_volt, func_tol=1e-3, interval_tol=0.0001, max_iter=20):

        fm= self.get_volt(amp_now) - target_volt

        #print("get fm: ",fm)

        if abs(fm)<func_tol: return amp_now

        if abs(fm)>0.8: return amp_now #if the voltage is too large

        if fm<-0.2:return amp_now+self.cal_amp_step*5

        if fm<-0.1:return amp_now+self.cal_amp_step*3

        if fm<0:return amp_now+self.cal_amp_step

        if fm>0.2:return amp_now-self.cal_amp_step*5

        if fm>0.1:return amp_now-self.cal_amp_step*3

        return amp_now-self.cal_amp_step
    

        # if fm>0:
        #     att1=att_low
        #     att2=att_low/2.0+att_high/2.0
        #     f1= self.get_volt(att1) - target_volt
        #     f2=fm
        # else:
        #     att2=att_high
        #     att1=att_low/2.0+att_high/2.0
        #     f1=fm
        #     f2= self.get_volt(att2) - target_volt

        # if f1 * f2 > 0:
        #     return (att2+att1)/2.0
        

        # for iteration in range(1, max_iter + 1):
        #     denominator = f1 - f2
        #     if abs(denominator)<1e-5:
        #         root = (att1 + att2) / 2
        #         return root

        #     att_mid = att1 + (att2 - att1) * (f1 / denominator)
        #     f_mid = self.get_volt(att_mid) - target_volt


        #     if abs(f_mid) < func_tol:
        #         print("meet precision threshold: ", f_mid)
        #         return att_mid

        #     if abs(att2 - att1) < interval_tol:
        #         print("meet interval threshold: ", f_mid)
        #         return att_mid

        #     if f1 * f_mid < 0:
        #         att2, f2 = att_mid, f_mid
        #     elif f2 * f_mid < 0:
        #         att1, f1 = att_mid, f_mid
        #     else:
        #         att_mid = (att_low+att_high) / 2
        #         return att_mid

        # root =  (att_low+att_high) / 2
        # print("Fail to find root", root)
        #return root


    # @kernel
    # def find_root_scan(self, att_low, att_high, target_volt, num_points=20):
    #     """
    #     Scans the attenuation range [att_low, att_high] at num_points randomized points,
    #     and uses a linear fit on the measured voltage differences to estimate the attenuation 
    #     that yields the target voltage.
    #     """
    #     xs = [0.0]*num_points
    #     fvals = [0.0]*num_points
    #     for _ in range(num_points):
    #         pt = att_low+(att_high-att_low)/(num_points-1)*_
    #         xs[_]=pt
    #         fvals[_]=self.get_volt(pt) - target_volt

    #     return self.estimate_root_from_fit(xs, fvals, att_low, att_high)

    

    # def estimate_root_from_fit(self, xs, fvals, att_low, att_high) -> float:
    #   #  import numpy as np

    #     coeffs = np.polyfit(xs, fvals, 2)
    #     a, b, c = coeffs
    #     discriminant = b * b - 4 * a * c
    #     if discriminant < 0 or abs(a) < 1e-12:
    #         idx = np.argmin(np.abs(fvals))
    #         return xs[idx]
    #     sqrt_disc = np.sqrt(discriminant)
    #     root1 = (-b + sqrt_disc) / (2 * a)
    #     root2 = (-b - sqrt_disc) / (2 * a)
    #     candidates = []
    #     if att_low <= root1 <= att_high:
    #         candidates.append(root1)
    #     if att_low <= root2 <= att_high:
    #         candidates.append(root2)
    #     if not candidates:
    #         idx = np.argmin(np.abs(fvals))
    #         return xs[idx]
    #     elif len(candidates) == 1:
    #         return candidates[0]
    #     else:
    #         mid = (att_low + att_high) / 2.0
    #         return candidates[0] if abs(candidates[0] - mid) < abs(candidates[1] - mid) else candidates[1]




    @kernel
    def run(self, amp_729_now, target_volt):
        
        self.core.break_realtime()
        self.seq.ion_store.run()  
        # set up the 729 nm laser parameters
        self.dds_729_sp.sw.off()
        self.dds_729_sp_aux.sw.off()
        self.dds_729_dp.sw.off()

        att_new_729= self.find_root(amp_729_now, target_volt=target_volt,  func_tol=5e-4,  max_iter=30)
        
        #att_new_729= self.find_root_scan(att_729_now+self.cal_att_range, att_729_now-self.cal_att_range, target_volt=target_volt)

        # self.exp.parameter_manager.set_param(
        #     "VdP2mode_SH/att_729_dp",
        #     att_new_729,
        #     "dB"
        #     )
        
        return att_new_729

       
