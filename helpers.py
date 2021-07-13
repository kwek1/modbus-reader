import minimalmodbus
from serial.tools import list_ports
import json


def find_ports():
    ports = [i.device for i in list_ports.comports()]
    return ports

def open_file(file):
    with open(file) as json_file:
        data = json.load(json_file)
    device_addresses = [int(i) for i in data.keys()]
    registers = {i:data[str(i)] for i in device_addresses}

    return device_addresses, registers


    
def open_devices(port, device_addresses):
    devices = {}
    for address in device_addresses:
        devices[address] = minimalmodbus.Instrument(port, address, 
                                                    close_port_after_each_call=False,
                                                    debug = False)
    devices[device_addresses[0]].serial.timeout = 0.5
    return devices

'''
# read temp from device 1
print("--- READING FROM DEVICE 1 ---")
print(devices[1].read_register(18181))
# read temp from device 3
print("--- READING FROM DEVICE 3 ---")
print(devices[3].read_register(18181))

while True:
    time_now = time.time()
    for i in device_addresses:
        for j in register:
            try:
                print(f"device {i} register{j}: {devices[i].read_register(j)}")
            except IOError:
                print("Failed to read from instrument")
    while time.time()-time_now < 1:
        continue
'''
#devices[3].read_register(18181)