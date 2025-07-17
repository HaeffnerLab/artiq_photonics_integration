import socket
import numpy as np
import time

def send_request():
    # Create a TCP/IP socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_address = ('192.168.169.133', 65432)
    client_socket.connect(server_address)

    try:
        while True:
            # Send request to the server
            start = time.time()
            message = b'request'
            client_socket.sendall(message)

            # Receive the response data from the server
            response_data = b''
            while len(response_data) < 10 * np.dtype(np.uint16).itemsize:  # Adjust according to the expected size of the array in bytes
                part = client_socket.recv(4096)  # Receive in larger chunks for performance
                response_data += part

            # byte_value=client_socket.recv(1)
            # if byte_value:
            # constant_value = int.from_bytes(byte_value, byteorder="big")
            # print(f"{constant_value:X}")
            # Convert bytes back to numpy array
            response_array = np.frombuffer(response_data, dtype=np.uint16)  # Reshape according to array shape
            # byte = 1
            # response = b
            print(f'Received array:\n{response_array}')
            print("time taken:",time.time() -start)
            print()

            # Pause or perform additional operations before the next request
            # a = input('Press Enter to send the next request...')
            # if a == "close":
            #     client_socket.close()
    finally:
        client_socket.close()

if __name__ == "__main__":
    send_request()