"""
Stark shift calculations for ion trap experiments.
This module provides functions to calculate Stark shifts for different excitation schemes
including single-pass, double-pass, and stimulated Raman transitions.
"""

from typing import Any
from artiq.experiment import *
import numpy as np


# Constants for matrix elements and calculations
MATRIX_ELEMENTS = {
    'am5_2': 1.0/144.0,  # Matrix element for |S1/2⟩ to |D-5/2⟩ transition
    'am1_2': 1.0/40.0,   # Matrix element for |S1/2⟩ to |D-1/2⟩ transition
    'a3_2': 1.0/720,     # Matrix element for |S1/2⟩ to |D3/2⟩ transition
    'b': 0.112/MHz       # Coupling constant (MHz^-1)
}

# Range factor for Rabi frequency calculations
RABI_FREQ_RANGE = 20


def stark_shift(parameter_manager: Any, freq_dp: float, freq_sp: float, Rabi_freq: float) -> float:
    """
    Calculate Stark shift for a given excitation configuration.
    
    This function computes the Stark shift considering transitions between different
    Zeeman levels in the S1/2 and D5/2 manifolds.
    
    Parameters:
    -----------
    parameter_manager : Any
        Object containing transition frequencies and other parameters.
    freq_dp : float
        Double-pass laser frequency in MHz.
    freq_sp : float
        Single-pass laser frequency in MHz.
    Rabi_freq : float
        Rabi frequency in MHz (without 2π).
        
    Returns:
    --------
    float
        Calculated Stark shift in MHz.
    """
    
    # Calculate transition frequencies relative to 729 nm
    Sm1_2_Dm5_2 = -parameter_manager.get_param("qubit/Sm1_2_Dm5_2")*2
    Sm1_2_Dm1_2 = -parameter_manager.get_param("qubit/Sm1_2_Dm1_2")*2
    Sm1_2_D3_2 = -parameter_manager.get_param("qubit/Sm1_2_D3_2")*2
    
    # Calculate AC frequency
    freq_ac = -freq_sp - freq_dp*2
    
    # Initialize delta_s_meta with constant term
    delta_s_meta = 2*MATRIX_ELEMENTS['b']*MATRIX_ELEMENTS['am1_2']
    
    # Calculate contributions from each transition
    for transition, matrix_elem in [
        (Sm1_2_Dm5_2, MATRIX_ELEMENTS['am5_2']),
        (Sm1_2_D3_2, MATRIX_ELEMENTS['a3_2']),
        (Sm1_2_Dm1_2, MATRIX_ELEMENTS['am1_2'])
    ]:
        if np.abs(freq_ac - transition) > Rabi_freq:
            delta_s_meta -= matrix_elem/(freq_ac - transition)
            if np.abs(freq_ac - transition) < RABI_FREQ_RANGE*Rabi_freq:
                delta_s_meta -= matrix_elem/(freq_ac - transition)
    
    # Calculate final Stark shift
    delta_s = Rabi_freq**2/4.0/MATRIX_ELEMENTS['am5_2']*delta_s_meta
    return delta_s


@rpc
def stark_shift_kernel(
    qubit_Sm1_2_Dm5_2: float,
    qubit_Sm1_2_Dm1_2: float,
    qubit_Sm1_2_D3_2: float,
    freq_dp: float,
    freq_sp: float,
    Rabi_freq: float
) -> float:
    """
    Calculate Stark shift in the kernel context.
    
    This is a kernel-compatible version of the Stark shift calculation that takes
    transition frequencies directly as parameters instead of using a parameter manager.
    
    Parameters:
    -----------
    qubit_Sm1_2_Dm5_2 : float
        |S1/2⟩ to |D-5/2⟩ transition frequency in MHz.
    qubit_Sm1_2_Dm1_2 : float
        |S1/2⟩ to |D-1/2⟩ transition frequency in MHz.
    qubit_Sm1_2_D3_2 : float
        |S1/2⟩ to |D3/2⟩ transition frequency in MHz.
    freq_dp : float
        Double-pass laser frequency in MHz.
    freq_sp : float
        Single-pass laser frequency in MHz.
    Rabi_freq : float
        Rabi frequency in MHz (without 2π).
        
    Returns:
    --------
    float
        Calculated Stark shift in MHz.
    """
    # Calculate transition frequencies relative to single-pass frequency
    Sm1_2_Dm5_2 = -qubit_Sm1_2_Dm5_2*2 - freq_sp
    Sm1_2_Dm1_2 = -qubit_Sm1_2_Dm1_2*2 - freq_sp
    Sm1_2_D3_2 = -qubit_Sm1_2_D3_2*2 - freq_sp
    
    # Calculate AC frequency
    freq_ac = -freq_sp - freq_dp*2
    
    # Initialize delta_s_meta with constant term
    delta_s_meta = 2*MATRIX_ELEMENTS['b']*MATRIX_ELEMENTS['am1_2']
    
    # Calculate contributions from each transition
    for transition, matrix_elem in [
        (Sm1_2_Dm5_2, MATRIX_ELEMENTS['am5_2']),
        (Sm1_2_D3_2, MATRIX_ELEMENTS['a3_2']),
        (Sm1_2_Dm1_2, MATRIX_ELEMENTS['am1_2'])
    ]:
        if np.abs(freq_ac - transition) > Rabi_freq:
            delta_s_meta -= matrix_elem/(freq_ac - transition)
            if np.abs(freq_ac - transition) < RABI_FREQ_RANGE*Rabi_freq:
                delta_s_meta -= matrix_elem/(freq_ac - transition)
    
    # Calculate final Stark shift
    delta_s = Rabi_freq**2/4.0/MATRIX_ELEMENTS['am5_2']*delta_s_meta
    return delta_s


@rpc
def stark_shift_SDF_kernel(Rabi_freq: float) -> float:
    """
    Calculate Stark shift for stimulated Raman transitions.
    
    This function computes the Stark shift for stimulated Raman transitions,
    which involves two light fields.
    
    Parameters:
    -----------
    Rabi_freq : float
        Rabi frequency in MHz (without 2π).
        
    Returns:
    --------
    float
        Calculated Stark shift in MHz (multiplied by 2 for two light fields).
    """
    # Initialize delta_s_meta with constant term
    delta_s_meta = 2*MATRIX_ELEMENTS['b']*MATRIX_ELEMENTS['am1_2']
    
    # Calculate Stark shift
    delta_s = Rabi_freq**2/4.0/MATRIX_ELEMENTS['am5_2']*delta_s_meta
    
    # Multiply by 2 for two light fields in SDF
    return delta_s*2
