# System imports 
from time import time, sleep

# Phidget specific imports
from Phidgets.PhidgetException import PhidgetException
import Phidgets.Devices.Bridge
from Phidgets.Phidget import PhidgetLogLevel

class Communicator(object):

    def __init__(self, series_prefix=''):
        self.connected = False


    def scan(self):
        pass

    def connect(self):
        pass

    def start_measurement(self):
        pass

    def disconnect(self):
        pass

    def receive(self, series, adjust):
        pass

    def send(self, data):
        pass

class Arduino(Communicator):
    """Class that communicates with the arduino board"""

    def __init__(self, series_prefix=''):

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
            self.ser = serial.Serial(port, 115200, timeout = 0.1)
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
        self.ser.write("go\n".encode())
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
            if time()-start_waiting > 1.0:
                self.ser.write((message+'\n').encode())
            # timeout the waiting after 10s
            if time()-start_waiting > 2.0:
                print ("Waiting for message %s timed out" %message)
                return

    def disconnect(self):
        sleep(0.1)
        self.ser.write("done\n".encode())
        sleep(0.1)
        self.wait_for_message("done")
        self.ser.flush()
        self.ser.close()
        self.connected = False

    def receive(self, series, adjust):
        start_time = time()
        while self.connected and time() - start_time < 0.02:
            line = self.ser.readline()
            values = line.split('\t')
            if len(values) == len(self.serie_names):
                for i, value in enumerate(values):
                    try:
                        value = float(value)
                    except ValueError:
                        break
                    if self.serie_names[i] in adjust:
                        series[self.serie_names[i]].append(value-adjust[self.serie_names[i]])
                    else:
                        series[self.serie_names[i]].append(value)
                break
            else:
                print line
        series['time'].append(time())

    def send(self, data):
        self.ser.write(("set %i\n"%int(data)).encode())
        print "Sent message"


class Bridge(Phidgets.Devices.Bridge.Bridge, Communicator):

    def BridgeAttached(self, e):
        self.attached = e.device

    def BridgeDetached(self, e):
        self.detached = e.device
    
    def BridgeData(self, e):
        if len(self.K) == 4 and len(self.offsets) == 4:
            self.latest_data[self.serie_names[e.index]].append(1000*self.K[e.index]*(float(e.value-self.offsets[e.index])))

    def BridgeError(self, e):
        try:
            source = e.device
            print "Bridge %i: Phidget Error %i: %s" %(source.getSerialNum(), e.eCode, e.description)
        except:
            print "Phidget Exception %i: %s" %(e.code, e.details)

    def __init__(self, series_prefix = ''):
        super(Bridge, self).__init__()
        self.attached = False
        self.detached = False
        self.connected = False
        self.K = []
        self.offsets = []

        self.serie_names = ["force_0", "force_1", "force_2", "force_3"]
        self.serie_names = ['_'.join([series_prefix,f]) for f in self.serie_names]
        self.setOnAttachHandler(self.BridgeAttached)
        self.setOnDetachHandler(self.BridgeDetached)
        self.setOnErrorhandler(self.BridgeError)
        self.setOnBridgeDataHandler(self.BridgeData)
        self.latest_data = {}
        for s in self.serie_names:
            self.latest_data[s] = []

    def scan(self):
        import subprocess
        from sys import platform as _platform

        bridges = {}
        if _platform == "linux" or _platform=="linux2":
            usb_devices = subprocess.check_output("lsusb -v | grep 'iProduct\|iSerial'", shell=True)
            lines = usb_devices.split('\n')
            bridges = dict([(' '.join(['PhidgetBridge', lines[i+1].split()[-1]]), lines[i+1].split()[-1]) for i, line in enumerate(lines) if 'PhidgetBridge' in line])

        return bridges

    def connect(self, port):
        # Don't try to connect if already connected
        if self.connected:
            return self.serie_names

        try:
            self.openPhidget(int(port))
        except PhidgetException as e:
            print("Phidget Exception %i: %s" %(e.code, e.details))
            self.closePhidget()
            return []
        try:
            self.waitForAttach(10000)
        except PhidgetException as e:
            print("Phidget Exception %i: %s" %(e.code, e.details))
            self.closePhidget()
            return []
        try:
            self.displayDeviceInfo()
            with open('calib_%i.conf'%(self.getSerialNum()), 'rb') as f:
                values = f.read().split('\n')
                self.K = [float(x) for i, x in enumerate(values) if x and i<4]
                self.offsets = [float(x) for i, x in enumerate(values) if x and i>3]
            self.setDataRate(20)
            for i in range(self.getInputCount()):
                self.setGain(i, Phidgets.Devices.Bridge.BridgeGain.PHIDGET_BRIDGE_GAIN_8)
            self.connected = True
        except PhidgetException as e:
            print("Phidget Exception %i: %s" %(e.code, e.details))
            self.closePhidget()
            return []
        return self.serie_names

    def start_measurement(self):
        if self.connected:
            for i in range(self.getInputCount()):
                self.setEnabled(i, True)

    def disconnect(self):
        for i in range(self.getInputCount()):
            self.setEnabled(2, False)
        self.closePhidget()
        self.connected = False
        pass

    def receive(self, series, adjust):
        if self.connected:
            if self.latest_data:
                for i in range(self.getInputCount()):
                    if self.serie_names[i] in adjust:
                        series[self.serie_names[i]].append(self.latest_data[self.serie_names[i]].pop()-adjust[self.serie_names[i]])
                    else:
                        series[self.serie_names[i]].append(self.latest_data[self.serie_names[i]].pop())

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
