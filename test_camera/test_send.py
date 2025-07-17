import socket
import pickle

# Client setup
HOST =  '192.168.169.122'  # Server IP address
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
# test_list = ["SDF",
#             {
#                 "freq_sp_RSB1": 80e6,
#                 "amp_sp_RSB1": 0.1,
#                 "freq_sp_BSB1": 80e6,
#                 "amp_sp_BSB1": 0.1
#             }
# ]
test_list = ["SingleTone",{"freq": 300e6,"amp": 0.1}]

def send_exp_para(HOST, PORT, param:list):
    # Create socket object
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((HOST, PORT))
    # Serialize the list using pickle
    data = pickle.dumps(test_list)

    # Send the serialized list
    client_socket.sendall(data)

    print(f"Sent list of floats: {test_list}")

    # Close the connection
    client_socket.close()

try:
    send_exp_para(HOST, PORT, test_list)
except Exception as e:
    print(e)
    print("AWG computer is not ready!!!")