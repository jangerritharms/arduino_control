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

# import communicator classes
from communicator import Arduino, Bridge

# Plotting and numerical calculation imports
import numpy as np
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

PLOTS = 4
LIMITS = {'counter': (0, 1000), 
          'yaxis': (0, 1023)}
COMS = [{'name': 'arduino', 'type': Arduino}, 
        #{'name': 'thrust_bridge', 'type': Bridge}, 
        #{'name': 'lift_bridge', 'type': Bridge} 
        ]

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
        layout = QtGui.QVBoxLayout(self.main_widget)
        com_row = QtGui.QHBoxLayout(self.main_widget)

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
        layout.addWidget(self.scanner)
        layout.addWidget(self.connecter)

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

        #self.arduino = Arduino(self.window)
        #self.thrust_bridge = Bridge()
        #self.lift_bridge = Bridge()

        # Create the communicators
        self.coms = {}
        for com in COMS:
            self.coms[com['name']] = com['type']()

        # Connecting buttons to functions
        self.window.connecter.clicked.connect(self.connect)
        self.window.scanner.clicked.connect(self.scan)

        # Structures to hold information
        self.port_list = {}
        self.series = {}
        self.saved = True

        # Scan for connected devices
        self.scan()

        self.x = np.linspace(-100, 0, 1000)
        self.test = 0 

        self.initializeMainLoop(100, 100, 100)

    def connect(self):

        for dev in COMS:
            self.window.com_status[dev['name']].setText("Connecting ...")

            port = self.port_list[str(self.window.port_chooser[dev['name']].currentText())]
     
            serie_names = self.coms[dev['name']].connect(port)

            for key in serie_names:
                if key not in self.series:
                    for i in range(PLOTS):
                        self.window.series_chooser[i].addItem(key)
                self.series[key] = []

            self.window.com_status[dev['name']].setText("Connected");

        self.window.connecter.setText("&Start Measurement");
        self.window.connecter.clicked.disconnect()
        self.window.connecter.clicked.connect(self.start_measurement)

    def start_measurement(self):

        if not self.saved:
            result = QtGui.QMessageBox.question(self.window, 'Save or Discard', 'Starting a new measurement series will discard all unsaved previous results. Save them now?', QtGui.QMessageBox.Save | QtGui.QMessageBox.Discard | QtGui.QMessageBox.Cancel)
            if result == QtGui.QMessageBox.Save: self.save()
            elif result == QtGui.QMessageBox.Discard: pass
            else: return

        for dev in COMS:
            self.coms[dev['name']].start_measurement()
            self.window.com_status[dev['name']].setText("Measuring");

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


    def scan(self):

        for dev in COMS:
            self.window.com_status[dev['name']].setText("&Scanning ... ")
            self.window.com_status[dev['name']].setStyleSheet("QLabel { background-color: yellow; color: white; padding-left: 5px}")

            QtGui.QApplication.processEvents()

            self.port_list[dev['name']] = self.coms[dev['name']].scan()

            for name in self.port_list[dev['name']]:
                print "name {0} port_chooser {1}".format(name, self.window.port_chooser[dev['name']].findText(name))
                if self.window.port_chooser[dev['name']].findText(name) == -1:
                    self.window.port_chooser[dev['name']].addItem(name)

            # Print status
            if len(self.port_list)>0:
                self.window.com_status[dev['name']].setText("%d devices found. Ready."%len(self.port_list))
                self.window.com_status[dev['name']].setStyleSheet("QLabel { background-color: green; color: white; padding-left: 5px}")
            else:
                self.window.com_status[dev['name']].setText("No Arduino found, please connect one via USB.")
                self.window.com_status[dev['name']].setStyleSheet("QLabel { background-color: red; color: white; padding-left: 5px}")


    def initializeMainLoop(self, receiveInterval, sendInterval, drawInterval):
        # Start getting information from the communicator
        for dev in COMS:
            timer = QtCore.QTimer(self.window)
            timer.timeout.connect(lambda: self.coms[dev['name']].receive(self.series))
            timer.start(receiveInterval)

        # Set update interval for drawing the data
        timer = QtCore.QTimer(self.window)
        timer.timeout.connect(self.update_figure)
        timer.start(drawInterval)

    def update_figure(self):
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

        import csv
        try:
            fname = QtGui.QFileDialog.getSaveFileName(self.window, 'Save Results', os.path.dirname(os.path.abspath(__file__)))
            writer = csv.writer(open(fname, 'wb'))
        except IOError:
            writer = csv.writer(open('result_%s.csv'%(datetime.now()), 'wb'))
        for key, value in self.series.items():
            writer.writerow([key, value])
        self.saved = True



if __name__=="__main__":
    c = Controller()
    c.run()
