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
from copy import deepcopy
from time import sleep, time
from datetime import datetime
from PyQt4 import QtGui, QtCore

# import communicator classes
from communicator import Arduino, Bridge

# Plotting and numerical calculation imports
import numpy as np
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from settings import PLOTS, COMS, LIMITS, SAMPLE_RATE, DRAW_RATE

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
        if self.y and min(self.y)<self.limits[0]: 
            self.limits = (self.limits[0]-0.5*self.limits[1]-self.limits[0], self.limits[1])
            self.axes.set_ybound(self.limits)
            redraw = True
        if self.y and max(self.y)>self.limits[1]: 
            self.limits = (self.limits[0], self.limits[1]+0.5*self.limits[1]-self.limits[0])
            self.axes.set_ybound(self.limits)
            redraw = True
        self.axes.draw_artist(self.axes.patch)
        self.axes.draw_artist(self.line)

        # repaint is much faster but does not redraw the axis labels and ticks
        if not redraw:
            self.repaint()
        else: 
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
        self.port_chooser = {}
        self.com_status = {}
        self.com_label = {}

        self.main_widget = QtGui.QWidget(self)
        full_layout = QtGui.QHBoxLayout(self.main_widget)
        layout = QtGui.QVBoxLayout(self.main_widget)
        control_layout = QtGui.QGridLayout(self.main_widget)
        com_row = QtGui.QHBoxLayout(self.main_widget)
        self.slider = QtGui.QSlider(self.main_widget)
        self.slider.setOrientation(QtCore.Qt.Vertical)
        separator = QtGui.QFrame()
        self.spinbox = QtGui.QSpinBox()
        separator.setFrameStyle(QtGui.QFrame.VLine)
        self.slider.setRange(1000, 2000);
        self.spinbox.setRange(1000, 2000);
        self.slider.valueChanged.connect(self.spinbox.setValue)
        self.spinbox.valueChanged.connect(self.slider.setValue)
        self.pitch_label = QtGui.QLabel(self.main_widget)
        self.yaw_label = QtGui.QLabel(self.main_widget)
        self.roll_label = QtGui.QLabel(self.main_widget)

        # Create plots
        for i in range(PLOTS):
            self.plotter.append(Plotter(100, parent=self.main_widget, width=5, height=4, dpi=100))
            self.series_label.append(QtGui.QLabel(self.main_widget))
            self.series_label[i].setText("Series %d: "%i)
            self.series_chooser.append(QtGui.QComboBox(self.main_widget))
            self.series_chooser[i].currentIndexChanged.connect(self.update_figure)

        # self.slider = QtGui.QSlider(self.main_widget)
        for dev in COMS:
            self.com_label[dev['name']] = QtGui.QLabel(self.main_widget)
            self.com_label[dev['name']].setText(dev['name']+' status: ')
            self.port_chooser[dev['name']] = QtGui.QComboBox(self.main_widget)
            self.com_status[dev['name']] = QtGui.QLabel(self.main_widget)
            self.com_status[dev['name']].setText("Unkown")

        self.connecter = QtGui.QPushButton("&Connect", self.main_widget)
        self.save = QtGui.QPushButton("&Save", self.main_widget)
        self.stop = QtGui.QPushButton("&Pause", self.main_widget)
        self.scanner = QtGui.QPushButton("&Rescan", self.main_widget)

        # Adding the components to the layout
        for dev in COMS:
            com_layout = QtGui.QGridLayout(self.main_widget)
            com_layout.addWidget(self.com_label[dev['name']], 0, 0)
            com_layout.addWidget(self.com_status[dev['name']], 0, 1)
            com_layout.addWidget(self.port_chooser[dev['name']], 1, 0, 1, 2)
            com_row.addLayout(com_layout)

        layout.addLayout(com_row)

        for i in range(int(np.sqrt(PLOTS))):
            j=0
            plot_row = QtGui.QHBoxLayout(self.main_widget)
            plot_layout = QtGui.QGridLayout(self.main_widget)
            while j < int(np.sqrt(PLOTS)):
                plot_layout.addWidget(self.series_label[i*int(np.sqrt(PLOTS))+j], j, 0)
                plot_layout.addWidget(self.series_chooser[i*int(np.sqrt(PLOTS))+j], j, 1)
                plot_row.addWidget(self.plotter[i*int(np.sqrt(PLOTS))+j])
                j += 1
            plot_row.addLayout(plot_layout)
            layout.addLayout(plot_row)
        plot_row = QtGui.QHBoxLayout(self.main_widget)
        plot_layout = QtGui.QGridLayout(self.main_widget)
        for i in range(PLOTS-int(np.sqrt(PLOTS))**2):
            plot_layout.addWidget(self.series_label[i], i, 0)
            plot_layout.addWidget(self.series_chooser[i], i, 1)
            plot_row.addWidget(self.plotter[i])
        plot_row.addLayout(plot_layout)
        layout.addLayout(plot_row)
        control_layout.addWidget(self.scanner, 0, 0, 1, 1)
        control_layout.addWidget(self.connecter, 1, 0, 1, 1)
        control_layout.addWidget(self.save, 2, 0, 1, 1)
        control_layout.addWidget(self.stop, 3, 0, 1, 1)
        control_layout.addWidget(self.slider, 4, 0, 5, 1)
        control_layout.addWidget(self.spinbox, 9, 0, 1, 1)
        control_layout.addWidget(self.pitch_label, 10, 0, 1, 1)
        control_layout.addWidget(self.yaw_label, 11, 0, 1, 1)
        control_layout.addWidget(self.roll_label, 12, 0, 1, 1)
        full_layout.addLayout(layout)
        full_layout.addWidget(separator)
        full_layout.addLayout(control_layout)

        self.pitch_label.setText("Pitch: ?")
        self.yaw_label.setText("Yaw: ?")
        self.roll_label.setText("Roll: ?")

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

        # Create the communicators
        self.coms = {}

        # Structures to hold information
        self.saved = True
        self.port_list = {}
        self.series = {}
        self.serie_adjust = {}
        self.res = False

        self.timers = []
        receive_funcs = []

        for i, com in enumerate(COMS):
            self.coms[com['name']] = com['type'](com['series_prefix'])
            self.timers.append(QtCore.QTimer(self.window))
            receive_funcs.append(self.receive(self.coms[com['name']]))

        for i in range(len(self.timers)):
            self.timers[-1].timeout.connect(receive_funcs[i])

        # Connecting buttons to functions
        self.window.connecter.clicked.connect(self.connect)
        self.window.save.clicked.connect(self.save)
        self.window.scanner.clicked.connect(self.scan)
        self.window.stop.clicked.connect(self.pause)
        self.window.slider.valueChanged.connect(self.sendSpeedValue)
        self.window.slider.valueChanged.connect(self.sendSpeedValue)

        # Scan for connected devices
        self.scan()

        self.x = np.linspace(-100, 0, 1000)
        self.test = 0 

    def sendSpeedValue(self):
        
        if self.coms['arduino'].connected:
            self.coms['arduino'].send(self.window.spinbox.value())


    def pause(self):
        self.state = deepcopy(self.series)

        self.figure_timer.stop()

        self.window.stop.clicked.disconnect()
        self.window.stop.clicked.connect(self.continu)
        self.window.stop.setText("&Continue")
        
    def continu(self):
        if not self.res:
            self.series = deepcopy(self.state)
        else:
            self.series = deepcopy(self.empty_series)
        self.res = False

        self.figure_timer.start()

        self.window.stop.clicked.disconnect()
        self.window.stop.clicked.connect(self.pause)
        self.window.stop.setText("&Pause")

    def connect(self):
        for dev in COMS:
            for dev2 in COMS:
                if not dev == dev2 and self.window.port_chooser[dev['name']].currentText() == self.window.port_chooser[dev2['name']].currentText():
                    print "Same device chosen, use different one"
                    return

        self.series['time'] = []
        for dev in COMS:
            self.window.com_status[dev['name']].setText("Connecting ...")

            if self.window.port_chooser[dev['name']].currentText():
                port = self.port_list[dev['name']][str(self.window.port_chooser[dev['name']].currentText())]
            else:
                result = QtGui.QMessageBox.warning(self.window, 'Save or Discard', 'One of the devices is not connected. Please connect all devices.', QtGui.QMessageBox.Ok)
                self.window.com_status[dev['name']].setText("Not connected")
                return
                
     
            serie_names = self.coms[dev['name']].connect(port)
            if serie_names == []:
                self.window.com_status[dev['name']].setStyleSheet("QLabel { background-color: red; color: white; padding-left: 5px}")
                self.window.com_status[dev['name']].setText("Not connected")
                return


            for key in serie_names:
                if key not in self.series:
                    for i in range(PLOTS):
                        self.window.series_chooser[i].addItem(key)
                self.series[key] = []

            self.window.com_status[dev['name']].setText("Connected");
            self.window.com_status[dev['name']].setStyleSheet("QLabel { background-color: green; color: white; padding-left: 5px}")

        self.window.connecter.setText("&Calibrate");
        self.window.connecter.clicked.disconnect()
        self.window.connecter.clicked.connect(self.calibrate)

    def start_measurement(self):

        if not self.saved:
            result = QtGui.QMessageBox.question(self.window, 'Save or Discard', 'Starting a new measurement series will discard all unsaved previous results. Save them now?', QtGui.QMessageBox.Save | QtGui.QMessageBox.Discard | QtGui.QMessageBox.Cancel)
            if result == QtGui.QMessageBox.Save: self.save()
            elif result == QtGui.QMessageBox.Discard: pass
            else: return

        self.initializeMainLoop(1000/SAMPLE_RATE, 1000/DRAW_RATE)

        self.window.connecter.setText("&Disconnect");
        self.window.connecter.clicked.disconnect()
        self.window.connecter.clicked.connect(self.disconnect)


    def disconnect(self):

        for dev in COMS:
            self.coms[dev['name']].disconnect()
            self.window.com_status[dev['name']].setText("Disconnected");
        self.window.connecter.setText("&Connect");
        self.window.connecter.clicked.disconnect()
        self.window.connecter.clicked.connect(self.connect)

    def receive(self, com):
        return lambda: com.receive(self.series, self.serie_adjust)

    def scan(self):

        for dev in COMS:
            self.window.com_status[dev['name']].setText("Scanning ... ")
            self.window.com_status[dev['name']].setStyleSheet("QLabel { background-color: yellow; color: white; padding-left: 5px}")

            QtGui.QApplication.processEvents()

            self.port_list[dev['name']] = self.coms[dev['name']].scan()

            # Remove all items before adding new ones
            self.window.port_chooser[dev['name']].clear()
            for name in self.port_list[dev['name']]:
                if self.window.port_chooser[dev['name']].findText(name) == -1:
                    self.window.port_chooser[dev['name']].addItem(name)

            # Print status
            if len(self.port_list[dev['name']])>0:
                self.window.com_status[dev['name']].setText("%d devices found. Ready."%len(self.port_list[dev['name']]))
                self.window.com_status[dev['name']].setStyleSheet("QLabel { background-color: green; color: white; padding-left: 5px}")
            else:
                self.window.com_status[dev['name']].setText("No device found")
                self.window.com_status[dev['name']].setStyleSheet("QLabel { background-color: red; color: white; padding-left: 5px}")


    def calibrate(self):
        self.empty_series = deepcopy(self.series)
        timer = QtCore.QTimer(self.window)
        timer.timeout.connect(self.update_angles)
        timer.start(1000/DRAW_RATE)

        for i in range(len(self.timers)):
            self.timers[i].start(1000/SAMPLE_RATE)

        for dev in COMS:
            self.coms[dev['name']].start_measurement()
            self.window.com_status[dev['name']].setText("Measuring");

        # Measure something even if arduino is not connected
        stime = time()
        while (time()-stime)< 2.0:
            QtGui.QApplication.processEvents()

        # wait for the accelerometer to stabilize
        if 'pitch' in self.series and 'yaw' in self.series and 'roll' in self.series:
            print "Waiting for the accelerometer to stabilize"
            i = 0
            while True:
                QtGui.QApplication.processEvents()
                if all([x<0.01 for x in np.diff(self.series['pitch'][-20:])]) \
                        and all([x<0.01 for x in np.diff(self.series['yaw'][-20:])]) \
                        and all([x<0.01 for x in np.diff(self.series['roll'][-20:])]):
                    i += 1
                    if i>=50:
                        break

        # also reset the force sensors here
        for value in self.series:
            if 'force' in value:
                self.serie_adjust[value] = sum(self.series[value])/len(self.series[value])
 
        self.window.connecter.setText("&Start Measurement");
        self.window.connecter.clicked.disconnect()
        self.window.connecter.clicked.connect(self.start_measurement)

    def initializeMainLoop(self, receiveInterval, drawInterval):
        if 'counter' in self.series:
            self.serie_adjust['counter'] = self.series['counter'][-1] 
        # Empty the measurement data
        self.series = deepcopy(self.empty_series)
        # Set update interval for drawing the data
        self.figure_timer = QtCore.QTimer(self.window)
        self.figure_timer.timeout.connect(self.update_figure)
        self.figure_timer.start(drawInterval)

    def update_angles(self):
        if 'yaw' in self.series and 'pitch' in self.series and 'roll' in self.series:
            self.window.yaw_label.setText("yaw: %f"%self.series['yaw'][-1])
            self.window.roll_label.setText("roll: %f"%self.series['roll'][-1])
            self.window.pitch_label.setText("pitch: %f"%self.series['pitch'][-1])

    def update_figure(self):
        start_time = time()
        for dev in COMS:
            if not self.coms[dev['name']].connected:
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
        self.pause()
        import csv
        try:
            fname = QtGui.QFileDialog.getSaveFileName(self.window, 'Save Results', os.path.dirname(os.path.abspath(__file__)))
            writer = csv.writer(open(fname, 'wb'))
        except IOError:
            writer = csv.writer(open('result_%s.csv'%(datetime.now()), 'wb'))
        for key, value in self.series.items():
            writer.writerow([key, value])
        self.saved = True
        result = QtGui.QMessageBox.question(self.window, 'Reset', 'Do you want to reset the measurement data?', QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)
        if result == QtGui.QMessageBox.Yes: self.reset()
        else: pass

    def reset(self):
        if 'counter' in self.series:
            self.serie_adjust['counter'] = self.series['counter'][-1] 
        self.res = True




if __name__=="__main__":
    c = Controller()
    c.run()
