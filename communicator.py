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

    def receive(self, series):
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

        print "Starting Arduino measurement"


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
                raise Exception("Waiting for message %s timed out" %message)

    def disconnect(self):
        sleep(1.0)
        self.ser.write("done".encode())
        sleep(1.0)
        self.wait_for_message("done")
        self.ser.flush()
        self.ser.close()
        self.connected = False

    def receive(self, series):
        print "Arduino receive"
        valid_lines = 0
        while self.connected and valid_lines < len(self.serie_names):
            line = self.ser.readline()
            if len(line)>2:
                series[self.serie_names[valid_lines]].append(float(line))
                valid_lines += 1

class Bridge(Phidgets.Devices.Bridge.Bridge, Communicator):

    def BridgeAttached(self, e):
        self.attached = e.device

    def BridgeDetached(self, e):
        self.detached = e.device
    
    def BridgeData(self, e):
        source = e.device
        self.latest_data.append(float(e.value))

    def BridgeError(self, e):
        try:
            source = e.device
            print "Bridge %i: Phidget Error %i: %s" %(source.getSerialNum(), e.eCode, e.description)
        except:
            print "Phidget Exception %i: %s" %(e.code, e.details)

    def __init__(self):
        super(Bridge, self).__init__()
        self.attached = False
        self.detached = False

        self.serie_names = ["force_0", "force_1", "force_2", "force_3"]
        self.setOnAttachHandler(self.BridgeAttached)
        self.setOnDetachHandler(self.BridgeDetached)
        self.setOnErrorhandler(self.BridgeError)
        self.setOnBridgeDataHandler(self.BridgeData)
        self.openPhidget()
        self.latest_data = []

    def scan(self):
        try:
            self.waitForAttach(10000)
        except PhidgetException:
            print "Could not find any bridge" 
        start_time = time()
        while not self.attached:
            if time()-start_time > 10.0:
                return ""

        print " ".join([self.getDeviceName(), str(self.getSerialNum())])
        return {" ".join([self.getDeviceName(), str(self.getSerialNum())]): self.getSerialNum()}

    def connect(self, port):
        self.displayDeviceInfo()
        self.setDataRate(100)
        self.setGain(2, Phidgets.Devices.Bridge.BridgeGain.PHIDGET_BRIDGE_GAIN_8)
        self.connected = True
        return self.serie_names

    def start_measurement(self):
        self.setEnabled(2, True)
        pass

    def disconnect(self):
        self.setEnabled(2, False)
        self.closePhidget()
        self.connected = False
        pass

    def receive(self, series):
        print "Bridge receive"
        if self.connected:
            if self.latest_data:
                series[self.serie_names[2]].append(self.latest_data.pop())

    #Information Display Function
    def displayDeviceInfo(self):
        print("|------------|----------------------------------|--------------|------------|")
        print("|- Attached -|-              Type              -|- Serial No. -|-  Version -|")
        print("|------------|----------------------------------|--------------|------------|")
        print("|- %8s -|- %30s -|- %10d -|- %8d -|" % (self.isAttached(), self.getDeviceName(), self.getSerialNum(), self.getDeviceVersion()))
        print("|------------|----------------------------------|--------------|------------|")
        print("Number of bridge inputs: %i" % (self.getInputCount()))
        print("Data Rate Max: %d" % (self.getDataRateMax()))
        print("Data Rate Min: %d" % (self.getDataRateMin()))
        print("Input Value Max: %d" % (self.getBridgeMax(0)))
        print("Input Value Min: %d" % (self.getBridgeMin(0)))
