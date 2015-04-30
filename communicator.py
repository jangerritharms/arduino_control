# System imports 
from time import time, sleep

# Phidget specific imports
from Phidgets.PhidgetException import PhidgetException
import Phidgets.Devices.Bridge
from Phidgets.Phidget import PhidgetLogLevel

class Communicator(object):

    def __init__(self):
        self.connected = False

    def scan(self):
        pass

    def connect(self):
        pass

    def start_measurement(self):
        pass

    def disconnect(self):
        pass

    def receive(self):
        pass

    def send(self, data):
        pass

class Arduino(Communicator):
    """Class that communicates with the arduino board"""

    def __init__(self):

        super(Arduino, self).__init__()
        self.serie_names = []

    def scan(self):

        # get a list of all usb serial devices 
        import subprocess
        import serial.tools.list_ports
        from sys import platform as _platform

        # For linux we first call lsusb to get descriptions of the connected
        # devices, next get all serial ports and find the intersection
        # between the two arrays while checking for the string Arduino
        if _platform == "linux" or _platform=="linux2":
            usb_devices = subprocess.check_output("lsusb", shell=True)
            ids = [dev.split()[5] for dev in usb_devices.split('\n') if dev]
            descriptions = [' '.join(dev.split()[6:]) for dev in usb_devices.split('\n') if dev]
            all_ports = serial.tools.list_ports.comports()
            port_list = dict([(description, port[0]) for id, description in zip(ids, descriptions) for port in all_ports if id in port[2] and 'Arduino' in description])
 
        return port_list
            

    def connect(self, port):

        import serial
        try:
            self.ser = serial.Serial(port, 9600, timeout = 5.0)
            self.ser.flush()
        except OSError:
            print "Port is not valid anymore"
            self.scan()

        # Wait for handshake with the arduino
        self.wait_for_message("series")
        self.serie_names = self.line.split()
        self.serie_names.pop(0)

        return self.serie_names
 

    def start_measurement(self):

        sleep(1.0)
        self.ser.write("go".encode())
        self.wait_for_message("go")

        self.connected = True


    def wait_for_message(self, message):
        start_waiting = time()
        self.line = ''
        while True:
            self.line = self.ser.readline()
            if len(self.line)>2 and self.line.split()[0] == message:
                break
            # retry sending the message if waiting for more than 5s
            if time()-start_waiting > 5.0:
                self.ser.write(message.encode())
            # timeout the waiting after 10s
            if time()-start_waiting > 10.0:
                raise TimeoutError("Waiting for message %s timed out" %message)

    def disconnect(self):
        sleep(1.0)
        self.ser.write("done".encode())
        sleep(1.0)
        self.wait_for_message("done")
        self.ser.flush()
        self.ser.close()
        self.connected = False

    def receive(self, series):
        valid_lines = 0
        while self.connected and valid_lines < len(self.serie_names):
            line = self.ser.readline()
            if len(line)>2:
                series[self.serie_names[valid_lines]].append(float(line))
                valid_lines += 1

class Bridge(Phidgets.Devices.Bridge.Bridge):

    def BridgeAttached(self, e):
        attached = e.device

    def BridgeDetached(self, e):
        detached = e.device

    def BridgeError(self, e):
        try:
            source = e.device
            print "Bridge %i: Phidget Error %i: %s" %(source.getSerialNum(), e.eCode, e.description)
        except:
            print "Phidget Exception %i: %s" %(e.code, e.details)
            


