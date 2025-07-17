"""
Transmitter module for AWG (Arbitrary Waveform Generator) communication.
This module handles sending experiment parameters to the AWG computer via TCP/IP.
"""

import socket
import pickle
from typing import Any, List

# Default connection settings
DEFAULT_HOST = '192.168.0.6'  # Server IP address
DEFAULT_PORT = 65432          # Port to connect to

def send_exp_para(data_packet: List[Any], 
                  host: str = DEFAULT_HOST, 
                  port: int = DEFAULT_PORT) -> None:
    """
    Send experiment parameters to the AWG computer via TCP/IP.
    
    Args:
        data_packet: List containing experiment parameters (e.g., ["SingleTone", {"freq": 80e6, "amp": 0.1}])
        host: The IP address of the AWG computer
        port: The port number to connect to
        
    Raises:
        Exception: If connection to AWG computer fails
    """
    try:
        # Create socket object
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((host, port))
        
        # Serialize the data using pickle
        data = pickle.dumps(data_packet)
        
        # Send the serialized data
        client_socket.sendall(data)
        
        # Close the connection
        client_socket.close()
        
    except Exception as e:
        print(f"Error: {e}")
        print("AWG computer is not ready!!!")

# Example usage:
# try:
#     send_exp_para(["SingleTone", {"freq": 80e6, "amp": 0.1}])
# except Exception as e:
#     print(e)
#     print("AWG computer is not ready!!!")