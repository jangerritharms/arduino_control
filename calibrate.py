#! /usr/bin/python

"""Copyright 2011 Phidgets Inc.
This work is licensed under the Creative Commons Attribution 2.5 Canada License.
To view a copy of this license, visit http://creativecommons.org/licenses/by/2.5/ca/
"""

__author__="Adam Stelmack"
__version__="2.1.8"
__date__ ="14-Jan-2011 2:29:14 PM"

#Basic imports
import sys
from time import sleep, time
#Phidget specific imports
from Phidgets.PhidgetException import PhidgetException
from Phidgets.Devices.Bridge import Bridge, BridgeGain
from Phidgets.Phidget import PhidgetLogLevel

measure_DATA = False
measure_MEAS = -1
DATA = [[], [], [], []]
MEAS = [[],[],[],[]]
offsets = []
K = []
printing = False

#Create an accelerometer object
try:
    bridge = Bridge()
except RuntimeError as e:
    print("Runtime Exception: %s" % e.details)
    print("Exiting....")
    exit(1)

#Information Display Function
def displayDeviceInfo():
    print("|------------|----------------------------------|--------------|------------|")
    print("|- Attached -|-              Type              -|- Serial No. -|-  Version -|")
    print("|------------|----------------------------------|--------------|------------|")
    print("|- %8s -|- %30s -|- %10d -|- %8d -|" % (bridge.isAttached(), bridge.getDeviceName(), bridge.getSerialNum(), bridge.getDeviceVersion()))
    print("|------------|----------------------------------|--------------|------------|")
    print("Number of bridge inputs: %i" % (bridge.getInputCount()))
    print("Data Rate Max: %d" % (bridge.getDataRateMax()))
    print("Data Rate Min: %d" % (bridge.getDataRateMin()))
    print("Input Value Max: %d" % (bridge.getBridgeMax(0)))
    print("Input Value Min: %d" % (bridge.getBridgeMin(0)))

#Event Handler Callback Functions
def BridgeAttached(e):
    attached = e.device
    print("Bridge %i Attached!" % (attached.getSerialNum()))

def BridgeDetached(e):
    detached = e.device
    print("Bridge %i Detached!" % (detached.getSerialNum()))

def BridgeError(e):
    try:
        source = e.device
        print("Bridge %i: Phidget Error %i: %s" % (source.getSerialNum(), e.eCode, e.description))
    except PhidgetException as e:
        print("Phidget Exception %i: %s" % (e.code, e.details))

def BridgeData(e):
    source = e.device
    if measure_DATA:
        DATA[e.index].append(float(e.value))
    if e.index == measure_MEAS:
        MEAS[e.index].append(float(e.value))
    if printing:
        if e.index ==2:
            print ("Sensor %i; Weight %f" %(e.index, K[e.index]*(e.value-offsets[e.index])))

#Main Program Code
try:
	#logging example, uncomment to generate a log file
    #bridge.enableLogging(PhidgetLogLevel.PHIDGET_LOG_VERBOSE, "phidgetlog.log")
	
    bridge.setOnAttachHandler(BridgeAttached)
    bridge.setOnDetachHandler(BridgeDetached)
    bridge.setOnErrorhandler(BridgeError)
    bridge.setOnBridgeDataHandler(BridgeData)
except PhidgetException as e:
    print("Phidget Exception %i: %s" % (e.code, e.details))
    print("Exiting....")
    exit(1)

print("Opening phidget object....")

try:
    bridge.openPhidget()
except PhidgetException as e:
    print("Phidget Exception %i: %s" % (e.code, e.details))
    print("Exiting....")
    exit(1)

print("Waiting for attach....")

try:
    bridge.waitForAttach(10000)
except PhidgetException as e:
    print("Phidget Exception %i: %s" % (e.code, e.details))
    try:
        bridge.closePhidget()
    except PhidgetException as e:
        print("Phidget Exception %i: %s" % (e.code, e.details))
        print("Exiting....")
        exit(1)
    print("Exiting....")
    exit(1)
else:
    displayDeviceInfo()

try:
    print("Set data rate to 8ms ...")
    bridge.setDataRate(8)
    sleep(2)

    print("Set Gain to 8...")
    bridge.setGain(0, BridgeGain.PHIDGET_BRIDGE_GAIN_8)
    bridge.setGain(1, BridgeGain.PHIDGET_BRIDGE_GAIN_8)
    bridge.setGain(2, BridgeGain.PHIDGET_BRIDGE_GAIN_8)
    bridge.setGain(3, BridgeGain.PHIDGET_BRIDGE_GAIN_8)
    sleep(2)

    print("Enable the Bridge input for reading data...")
    bridge.setEnabled(0, True)
    bridge.setEnabled(1, True)
    bridge.setEnabled(2, True)
    bridge.setEnabled(3, True)
    sleep(2)

except PhidgetException as e:
    print("Phidget Exception %i: %s" % (e.code, e.details))
    try:
        bridge.closePhidget()
    except PhidgetException as e:
        print("Phidget Exception %i: %s" % (e.code, e.details))
        print("Exiting....")
        exit(1)
    print("Exiting....")
    exit(1)

print("Remove all forces from sensors and press Enter to begin Calibration. ....")

chr = sys.stdin.read(1)

print "Calibration in progress ",
measure_DATA = True
while True:
    # Read Input to end the calibration
    if all([len(li)>1000 for li in DATA]):
        break
    print ".",
    sleep(0.5)
measure_DATA = False

print DATA[0][0]
offsets = [sum(li)/len(li) for li in DATA]
print offsets[0]

print "Next we need to attach a known force to each sensor"
OK = False
while not OK:
    print "Give the weight you will attach in grams"
    weight = sys.stdin.readline()
    try:
        weight = float(weight)
        if not weight>0 or not weight<1000:
            raise ValueError
    except ValueError:
        print "Please use only digits and type a number between 0 and 1000"
        continue
    OK = True


weight = weight/ 1000
for i in range(bridge.getInputCount()):
    print "Attach weight to Sensor %d and press Enter" %i
    sys.stdin.read(1)
    measure_MEAS = i
    print "Measuring ",
    while len(MEAS[i])<1000:
        print ".",
        sleep(0.5)
    measure_MEAS = -1
    print "Done with measuring sensor %d" %i
    sleep(0.5)

print "Done measuring. I will now calculate the sensor constants"

meas = [sum(li)/len(li) for li in MEAS]
print "weight ", weight
print "offset ", offsets[0]
print "meas ", meas[0]
K = [weight/(m-o) for m, o in zip(meas, offsets)]

calib_file = open("calib_{0}.conf".format(bridge.getSerialNum()), 'wb')
for k in K:
    print>>calib_file, k
for o in offsets:
    print>>calib_file, o
calib_file.close()
print "Saved results"

printing = True
bridge.setDataRate(500)
print "Printing live output. Press Enter to quit"
sys.stdin.read(1)

print("Closing...")

try:
    print("Disable the Bridge input for reading data...")
    bridge.setEnabled(0, False)
    bridge.setEnabled(1, False)
    bridge.setEnabled(2, False)
    bridge.setEnabled(3, False)
    sleep(2)
except PhidgetException as e:
    print("Phidget Exception %i: %s" % (e.code, e.details))
    try:
        bridge.closePhidget()
    except PhidgetException as e:
        print("Phidget Exception %i: %s" % (e.code, e.details))
        print("Exiting....")
        exit(1)
    print("Exiting....")
    exit(1)

try:
    bridge.closePhidget()
except PhidgetException as e:
    print("Phidget Exception %i: %s" % (e.code, e.details))
    print("Exiting....")
    exit(1)

print("Done.")
exit(0)
