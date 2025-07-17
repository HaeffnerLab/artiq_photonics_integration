# """
# RF Modulator module for controlling RF voltage levels via VISA communication.
# This module provides an interface to control RF voltage levels through a power supply.
# """

# import time
# from typing import Optional
# import pyvisa
# from pyvisa.resources import Resource

# class rf_modulator:
#     """
#     Class for controlling RF voltage levels through a power supply.
    
#     This class manages the connection and control of a power supply for RF modulation,
#     providing methods to set different voltage levels for various RF states.
#     """
    
#     def __init__(self, ip_address: str = "192.168.0.2"):
#         """
#         Initialize the RF Modulator.
        
#         Args:
#             ip_address: IP address of the power supply
#         """
#         self.ip_address = ip_address
#         self.resource_string = f"TCPIP0::{self.ip_address}::INSTR"
#         self.rm = pyvisa.ResourceManager()
        
#         # Voltage levels for different states
#         self.rf_high = 0.0  # Option 1
#         self.rf_low = 0.0  # Option 0
#         self.rf_dump = 1.7  # Option 2
#         self.rf_load = 1.3 # Option 3
        
#         self.instrument: Optional[Resource] = None
    
#     def connect_rf(self) -> None:
#         """
#         Establish connection to the RF power supply.
        
#         Attempts to connect to the power supply and set initial voltage.
#         Retries connection if it fails.
        
#         Raises:
#             Exception: If connection fails after multiple attempts
#         """
#         while True:
#             try:
#                 self.instrument = self.rm.open_resource(self.resource_string)
#                 self.instrument.write(f"VOLT {self.rf_low}")
#                 self.instrument.write("OUTP ON")
#                 print("Connected successfully!")
#                 break  
#             except Exception as e:
#                 print(f"Connection failed: {e}. Retrying in 1 second...")
#                 time.sleep(1)

#     def set_voltage(self, voltage: int = 1) -> None:
#         """
#         Set the RF voltage level based on the specified option.
        
#         Args:
#             voltage: Voltage option (0: low, 1: high, 2: dump, 3: load)
            
#         Raises:
#             Exception: If voltage setting fails after multiple attempts
#         """
#         pass
#         while True:
#             try:
#                 self.instrument.write("INST:NSEL 2")
#                 self.instrument.write("VOLT 1")

#                 self.instrument.write("INST:NSEL 3")
                
#                 voltage_map = {
#                     1: self.rf_high,
#                     0: self.rf_low,
#                     3: self.rf_load,
#                     2: self.rf_dump
#                 }
                
#                 if voltage in voltage_map:
#                     self.instrument.write(f"VOLT {voltage_map[voltage]}")
#                 else:
#                     print('WARNING: Invalid Voltage Option, Setting to Low Voltage')
#                     self.instrument.write(f"VOLT {self.rf_low}")

#                 self.instrument.write("OUTP ON")
#                 break

#             except Exception as e:
#                 print(f"Set Volt Failed: {e}. Retrying in 1 second...")
#                 time.sleep(1)
    
#     def close(self) -> None:
#         """
#         Close the connection to the power supply.
        
#         Safely closes both the instrument and resource manager connections.
#         """
#         try:
#             if self.instrument:
#                 self.instrument.close()
#             self.rm.close()
#         except Exception:
#             pass
    
#     def __del__(self) -> None:
#         """
#         Destructor to ensure proper cleanup of resources.
#         """
#         self.close()