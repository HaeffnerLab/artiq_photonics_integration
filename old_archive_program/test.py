import serial
import serial.tools.list_ports

# Get a list of all available ports
ports = list(serial.tools.list_ports.comports())

# Print details of each port
for port in ports:
    print(f"Port: {port.device}, Description: {port.description}, HWID: {port.hwid}")


ser = serial.Serial('/dev/serial/by-id/usb-Prolific_Technology_Inc._USB-Serial_Controller_AZBRb132J02-if00-port0', 9600) 
#serial.Serial('/dev/serial/by-path/pci-0000:00:14.0-usb-0:6:1.0-port0', 9600) #//port & baud rate

#Write Current
ser.write(b'CURRent 5\n') #Set to 3 A
#Write Voltage
ser.write(b'VOLTage 3.5\n') #Set to 3 V
ser.write(b'OUTPut 1\n')



print(ser.readline())