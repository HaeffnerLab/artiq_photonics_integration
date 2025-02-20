import socket
import pickle

# Client setup
HOST =  '192.168.0.2'  # Server IP address
PORT = 65432              # Port to connect to

# List of floats to send
# float_list = {
#     "sequence_name" : "SDF",
#     "freq_RSB": 80e6+0.5e6,
#     "freq_BSB": 80e6-0.5e6,
#     "amp_RSB": 0.1,
#     "amp_BSB": 0.1,
# }

#float_list = ["SingleTone",{"freq": 80e6,"amp": 0.1}]

# float_list = ["SDF",
#             {
#                 "freq_sp_RSB1": 80e6,
#                 "amp_sp_RSB1": 0.1,
#                 "freq_sp_BSB1": 80e6,
#                 "amp_sp_BSB1": 0.1
#             }
# ]

def send_exp_para(data_packet, HOST=HOST, PORT=PORT) -> None:

    try:
        # Create socket object
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((HOST, PORT))
        # Serialize the list using pickle
        data = pickle.dumps(data_packet)

        # Send the serialized list
        client_socket.sendall(data)

        #print(f"Sent list of floats: {data_packet}")
        # Close the connection
        client_socket.close()
    except Exception as e:
        print(e)
        print("AWG computer is not ready!!!")

# try:
#     send_exp_para(["SingleTone",{"freq": 80e6,"amp": 0.1}])
# except Exception as e:
#     print(e)
#     print("AWG computer is not ready!!!")