#!/usr/bin/env python3
import pyvisa
import sys
class rf_modulator:
    #ip_address = "192.168.0.2"

    resource_string = f"TCPIP0::192.168.0.2::INSTR"

    def __init__(self):
        self.rm = pyvisa.ResourceManager()
        self.instrument = self.rm.open_resource(self.resource_string)

    def set_voltage(
            self,
            voltage=1.0
        ):

        # Select channel 3 on the power supply
        self.instrument.write("INST:NSEL 3")
        self.instrument.write(f"VOLT {voltage}")
        self.instrument.write("OUTP ON")
    
    def __del__(self):
        self.instrument.close()
        self.rm.close()

