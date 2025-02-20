from artiq.experiment import *
import numpy as np

def stark_shift(parameter_manager, freq_dp, freq_sp, Rabi_freq):

    #parameter manager for getting qutip frequencies
    #rabi_freq without 2pi
    #freq in sp frequency 

    Sm1_2_Dm5_2=-parameter_manager.get_param("qubit/Sm1_2_Dm5_2")*2-80*MHz
    Sm1_2_Dm1_2=-parameter_manager.get_param("qubit/Sm1_2_Dm1_2")*2-80*MHz
    Sm1_2_D3_2=-parameter_manager.get_param("qubit/Sm1_2_D3_2")*2-80*MHz

    freq_ac = -freq_sp-freq_dp*2

    #matrix element
    am5_2=1.0/144.0
    am1_2=1.0/40.0
    a3_2=1.0/720
    b=0.112/MHz #(MHz^-1)

    # the range of calculating is from 1 to 20 times the rabi frequency

    delta_s_meta=2*b*am1_2

   

    if np.abs(freq_ac-Sm1_2_Dm5_2)>Rabi_freq:
        delta_s_meta-=am5_2/(freq_ac-Sm1_2_Dm5_2)
        if np.abs(freq_ac-Sm1_2_Dm5_2)<20*Rabi_freq:
            delta_s_meta-=am5_2/(freq_ac-Sm1_2_Dm5_2)

    if np.abs(freq_ac-Sm1_2_D3_2)>Rabi_freq:
        
        delta_s_meta-=a3_2/(freq_ac-Sm1_2_D3_2)
        if np.abs(freq_ac-Sm1_2_D3_2)<20*Rabi_freq:
            delta_s_meta-=a3_2/(freq_ac-Sm1_2_D3_2)

    if np.abs(freq_ac-Sm1_2_Dm1_2)>Rabi_freq:
        
        delta_s_meta-=am1_2/(freq_ac-Sm1_2_Dm1_2)
        if np.abs(freq_ac-Sm1_2_Dm1_2)<20*Rabi_freq:
            delta_s_meta-=am1_2/(freq_ac-Sm1_2_Dm1_2)
            
    delta_s=Rabi_freq**2/4.0/am5_2*delta_s_meta
    return delta_s

@rpc
def stark_shift_kernel(qubit_Sm1_2_Dm5_2, 
                       qubit_Sm1_2_Dm1_2, 
                       qubit_Sm1_2_D3_2, 
                       freq_dp, 
                       freq_sp, 
                       Rabi_freq)->float:

    #parameter manager for getting qutip frequencies
    #rabi_freq without 2pi
    #freq in sp frequency 

    Sm1_2_Dm5_2=-qubit_Sm1_2_Dm5_2*2-80*MHz
    Sm1_2_Dm1_2=-qubit_Sm1_2_Dm1_2*2-80*MHz
    Sm1_2_D3_2=-qubit_Sm1_2_D3_2*2-80*MHz

    freq_ac = -freq_sp-freq_dp*2

    #matrix element
    am5_2=1.0/144.0
    am1_2=1.0/40.0
    a3_2=1.0/720
    b=0.112/MHz #(MHz^-1)

    # the range of calculating is from 1 to 20 times the rabi frequency

    delta_s_meta=2*b*am1_2

   

    if np.abs(freq_ac-Sm1_2_Dm5_2)>Rabi_freq:
        delta_s_meta-=am5_2/(freq_ac-Sm1_2_Dm5_2)
        if np.abs(freq_ac-Sm1_2_Dm5_2)<20*Rabi_freq:
            delta_s_meta-=am5_2/(freq_ac-Sm1_2_Dm5_2)

    if np.abs(freq_ac-Sm1_2_D3_2)>Rabi_freq:
        
        delta_s_meta-=a3_2/(freq_ac-Sm1_2_D3_2)
        if np.abs(freq_ac-Sm1_2_D3_2)<20*Rabi_freq:
            delta_s_meta-=a3_2/(freq_ac-Sm1_2_D3_2)

    if np.abs(freq_ac-Sm1_2_Dm1_2)>Rabi_freq:
        
        delta_s_meta-=am1_2/(freq_ac-Sm1_2_Dm1_2)
        if np.abs(freq_ac-Sm1_2_Dm1_2)<20*Rabi_freq:
            delta_s_meta-=am1_2/(freq_ac-Sm1_2_Dm1_2)
            
    delta_s=Rabi_freq**2/4.0/am5_2*delta_s_meta
    return delta_s


@rpc
def stark_shift_SDF_kernel(Rabi_freq)->float:

    #parameter manager for getting qutip frequencies
    #rabi_freq without 2pi
    #freq in sp frequency 
    #matrix element
    am5_2=1.0/144.0
    am1_2=1.0/40.0
    a3_2=1.0/720
    b=0.112/MHz #(MHz^-1)

    # the range of calculating is from 1 to 20 times the rabi frequency

    delta_s_meta=2*b*am1_2
    delta_s=Rabi_freq**2/4.0/am5_2*delta_s_meta
    return delta_s*2 #*2 because of SDF has two light
