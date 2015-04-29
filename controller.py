# -*- coding: utf-8 -*-
"""
Created on Sun Apr 19 18:35:48 2015

@author: jan
"""

#!/usr/bin/env python

from __future__ import unicode_literals
import sys
import os
import random
from time import sleep, time
from datetime import datetime
from PyQt4 import QtGui, QtCore

import numpy as np
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

PLOTS = 4
LIMITS = {'counter': (0, 1000), 
          'yaxis': (0, 1023)}

class Plotter(FigureCanvas):
    """A canvas that updates itself every second with a new plot.
        
        time_length: amount of time in seconds to display in the past
        udpateInterval: Time step of measurement in milliseconds for updating the graph
        parent: Parent QT widget to house the figure
        width: Amount of blocks in the GUI in horizontal direction
        height: Amount of blocks in the GUI in vertical direction
        dpi: Resolution of the figure
        
    """
    def __init__(self, time_length, parent=None, width=5, height=4, dpi=100, *args, **kwargs):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_axes([0.17, 0.15, 0.80, 0.8])
        self.fig.patch.set_facecolor('white')
        
        # Create a figure canvas inside the GUI, set parent qtwidget
        FigureCanvas.__init__(self, self.fig)
        self.setParent(parent)

        FigureCanvas.setSizePolicy(self,
                                   QtGui.QSizePolicy.Expanding,
                                   QtGui.QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)
        
        # Create data array
        self.x = []
        self.y = []
        self.limits = ()
    
        # create a line to update consequently
        self.line, = self.axes.plot(self.x, self.y)
        self.background = self.copy_from_bbox(self.axes.bbox)
        self.axes.set_xlabel("Time")
        self.axes.set_xbound(-101, 1)
    
    def update_figure(self, y):
        redraw = False
        # update data
        self.y = y
        self.x = np.linspace(-len(y)/10., 0, len(y))
        self.line.set_xdata(self.x)
        self.line.set_ydata(self.y)
        if min(self.y)<self.limits[0]: 
            self.limits = (self.limits[0]-0.5*self.limits[1]-self.limits[0], self.limits[1])
            self.axes.set_ybound(self.limits)
            redraw = True
        if max(self.y)>self.limits[1]: 
            self.limits = (self.limits[0], self.limits[1]+0.5*self.limits[1]-self.limits[0])
            self.axes.set_ybound(self.limits)
            redraw = True
        self.axes.draw_artist(self.axes.patch)
        self.axes.draw_artist(self.line)

        # repaint is much faster but does not redraw the axis labels and ticks
        if not redraw:
            self.repaint()
        else: 
            print 'hello world'
            self.draw()

class ApplicationWindow(QtGui.QMainWindow):
    def __init__(self, parentQuit):

        # Create the main window
        QtGui.QMainWindow.__init__(self)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setWindowTitle("Motor Central Control")
        self.parentQuit = parentQuit

        # Create the menu structure
        self.file_menu = QtGui.QMenu('&File', self)
        self.file_menu.addAction('&Quit', self.fileQuit,
                                 QtCore.Qt.CTRL + QtCore.Qt.Key_Q)
        self.menuBar().addMenu(self.file_menu)
        self.help_menu = QtGui.QMenu('&Help', self)
        self.menuBar().addSeparator()
        self.menuBar().addMenu(self.help_menu)
        self.help_menu.addAction('&About', self.about)

        # Create all the required widgets and layouts
        self.plotter = []
        self.series_chooser = []
        self.series_label = []
        self.main_widget = QtGui.QWidget(self)
        layout = QtGui.QGridLayout(self.main_widget)
        sub_layout = QtGui.QGridLayout(self.main_widget)
        for i in range(PLOTS):
            self.plotter.append(Plotter(100, parent=self.main_widget, width=5, height=4, dpi=100))
            self.series_label.append(QtGui.QLabel(self.main_widget))
            self.series_label[i].setText("Series %d: "%i)
            self.series_chooser.append(QtGui.QComboBox(self.main_widget))
            self.series_chooser[i].currentIndexChanged.connect(self.update_figure)
        self.slider = QtGui.QSlider(self.main_widget)
        self.port_chooser = QtGui.QComboBox(self.main_widget)
        self.status = QtGui.QLabel(self.main_widget)
        self.slider.setOrientation(QtCore.Qt.Horizontal)
        self.connecter = QtGui.QPushButton("&Connect", self.main_widget)
        self.scanner = QtGui.QPushButton("&Rescan", self.main_widget)

        # Adding the components to the layout
        layout.addWidget(self.status, 0, 0, 1, 1 if PLOTS<=1 else  2)
        layout.addWidget(self.scanner, 0, 1 if PLOTS<=1 else  2, 1, 1);
        layout.addWidget(self.port_chooser, 1, 0, 1, 1 if PLOTS<=1 else  2)
        layout.addWidget(self.connecter, 1, 1 if PLOTS<=1 else  2, 1, 1)
        for i in range(PLOTS):
            layout.addWidget(self.plotter[i], 2+i/2, i%2)
            sub_layout.addWidget(self.series_label[i], i, 0, 1, 1)
            sub_layout.addWidget(self.series_chooser[i], i, 1, 1, 1)
        layout.addWidget(self.slider, 2+PLOTS/2+PLOTS%2, 0, 1, 1 if PLOTS<=1 else  2)
        layout.addLayout(sub_layout, 2, 1 if PLOTS<=1 else  2, PLOTS/2+PLOTS%2, 1)

        self.main_widget.setFocus()
        self.setCentralWidget(self.main_widget)
          
        # Create data array
        self.x = np.linspace(-100, 0, 100/100*1000)
        self.test = 0
    
    def update_figure(self):
        for i in range(PLOTS):
            self.plotter[i].axes.set_ylabel(self.series_chooser[i].currentText())
            if self.series_chooser[i].currentText():
                self.plotter[i].limits = LIMITS[str(self.series_chooser[i].currentText())]
                self.plotter[i].axes.set_ybound(self.plotter[i].limits)
                self.plotter[i].draw()

    def fileQuit(self):
        self.parentQuit()
        QtGui.qApp.closeAllWindows()

    def closeEvent(self, ce):
        self.fileQuit()

    def about(self):
        QtGui.QMessageBox.about(self, "About",
                """BirdPlane Test Setup controller""")


class Controller:
    """Parent class for all other components. Will create the window, initialize Plotter and Communicater module and get all the Settings"""

    def __init__(self):
        

        # Create qt context and window
        self.qApp = QtGui.QApplication(sys.argv)
        self.window = ApplicationWindow(self.onQuit)

        # Show the window
        self.window.show()
        self.window.raise_()

        self.port_list = {}
        self.series = {}
        self.saved = True

        # Check if Arduino is connected and open the Connector
        self.com = Communicator(self.window)
        self.window.connecter.clicked.connect(self.connect)
        self.window.scanner.clicked.connect(self.scan)

        self.scan()

        # Determine the fields from Arduino
        self.x = np.linspace(-100, 0, 1000)
        self.test = 0 

        self.initializeMainLoop(100, 100, 100)

    def connect(self):

        self.window.status.setText("Connecting ...")

        port = self.port_list[str(self.window.port_chooser.currentText())]
        
        serie_names = self.com.init_connection(port)

        for key in serie_names:
            if key not in self.series:
                for i in range(PLOTS):
                    self.window.series_chooser[i].addItem(key)
            self.series[key] = []

        self.window.status.setText("Connected");
        self.window.connecter.setText("&Start Measurement");
        self.window.connecter.clicked.disconnect()
        self.window.connecter.clicked.connect(self.start_measurement)

    def start_measurement(self):

        if not self.saved:
            result = QtGui.QMessageBox.question(self.window, 'Save or Discard', 'Starting a new measurement series will discard all unsaved previous results. Save them now?', QtGui.QMessageBox.Save | QtGui.QMessageBox.Discard | QtGui.QMessageBox.Cancel)
            if result == QtGui.QMessageBox.Save: self.save()
            elif result == QtGui.QMessageBox.Discard: pass
            else: return

        self.com.start_measurement()

        self.window.status.setText("Measuring");
        self.window.connecter.setText("&Disconnect");
        self.window.connecter.clicked.disconnect()
        self.window.connecter.clicked.connect(self.disconnect)


    def disconnect(self):

        self.com.disconnect()

        self.window.status.setText("Disconnected");
        self.window.connecter.setText("&Connect");
        self.window.connecter.clicked.disconnect()
        self.window.connecter.clicked.connect(self.connect)


    def scan(self):

        self.window.status.setText("&Scanning ... ")
        self.window.status.setStyleSheet("QLabel { background-color: yellow; color: white; padding-left: 5px}")

        QtGui.QApplication.processEvents()

        self.port_list = self.com.scan()

        for name in self.port_list:
            self.window.port_chooser.addItem(name)

        # Print status
        if len(self.port_list)>0:
            self.window.status.setText("%d devices found. Ready."%len(self.port_list))
            self.window.status.setStyleSheet("QLabel { background-color: green; color: white; padding-left: 5px}")
        else:
            self.window.status.setText("No Arduino found, please connect one via USB.")
            self.window.status.setStyleSheet("QLabel { background-color: red; color: white; padding-left: 5px}")


    def initializeMainLoop(self, receiveInterval, sendInterval, drawInterval):
        # Start getting information from the communicator
        timer = QtCore.QTimer(self.window)
        timer.timeout.connect(lambda: self.com.receive(self.series))
        timer.start(receiveInterval)

        # Set update interval for drawing the data
        timer = QtCore.QTimer(self.window)
        timer.timeout.connect(self.update_figure)
        timer.start(drawInterval)

    def update_figure(self):
        if not self.com.connected:
            return
        self.saved = False;
        for i in range(PLOTS):
            if (len(self.series[str(self.window.series_chooser[i].currentText())])<1000):
                self.window.plotter[i].update_figure(self.series[str(self.window.series_chooser[i].currentText())])
            else:
                self.window.plotter[i].update_figure(self.series[str(self.window.series_chooser[i].currentText())][-1000:])

    def run(self):
        try:
            self.qApp.exec_()
        except:
            self.window.fileQuit()

    def onQuit(self):
        if not self.saved:
            result = QtGui.QMessageBox.question(self.window, 'Save or Discard', 'There are unsaved results which will be lost if you close the program. Save them now?', QtGui.QMessageBox.Save | QtGui.QMessageBox.Discard | QtGui.QMessageBox.Cancel)
            if result == QtGui.QMessageBox.Save: self.save()
            elif result == QtGui.QMessageBox.Discard: pass
            else: return

    def save(self):

        import csv
        try:
            fname = QtGui.QFileDialog.getSaveFileName(self.window, 'Save Results', os.path.dirname(os.path.abspath(__file__)))
            
            writer = csv.writer(open(fname, 'wb'))
        except IOError:
            writer = csv.writer(open('result_%s.csv'%(datetime.now()), 'wb'))
        for key, value in self.series.items():
            writer.writerow([key, value])
        self.saved = True


class Communicator:
    """Class that communicates with the arduino board"""

    def __init__(self, window):

        self.connected = False
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
            

    def init_connection(self, port):

        import serial
        try:
            self.ser = serial.Serial(port, 9600)
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
        self.line = ''
        while True:
            self.line = self.ser.readline()
            if len(self.line)>2 and self.line.split()[0] == message:
                break;

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

if __name__=="__main__":
    c = Controller()
    c.run()
