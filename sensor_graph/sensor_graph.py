import sys
import traceback
import os
import time
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import * 
from PyQt5.QtWidgets import QMainWindow, QApplication, QWidget, QAction, QTableWidget,QTableWidgetItem,QVBoxLayout,QLabel
from PyQt5.QtCore import pyqtSlot,Qt,QTimer, QDateTime
from PyQt5.QtGui import * 
from PyQt5.QtGui import QIcon,QPixmap, QPalette
import pyqtgraph as pg
from pyqtgraph import PlotWidget, plot
import INA219
from INA219 import INA219

pg.setConfigOption('background', 'w')
pg.setConfigOption('foreground', 'k')

GRAPH_SAMPLES = 1000
SAMPLING_TIME = 10
FONT_SIZE = 40
R_SHUNT = 0.1

sensor = INA219(0x80, R_SHUNT)            

def create_graph( name ):
    return pg.PlotWidget(title=name)
    
def update_graph( graph_name, data, y_range ):
    graph_name.clear()
    if len(data) > GRAPH_SAMPLES:
        data = data[-GRAPH_SAMPLES:]
    graph_name.setYRange(0, y_range)
    graph_name.plot(range(1,len(data)+1), data)

class MainWindow(QMainWindow):
    def __init__(self, project, parent=None):
        
        super(MainWindow, self).__init__(parent)
        
        self.scrollArea = QScrollArea(widgetResizable=True)
        self.setCentralWidget(self.scrollArea)
        self.setWindowTitle(project)
        
        content_widget = QWidget()
        self.scrollArea.setWidget(content_widget)
        self._lay = QGridLayout(content_widget)

        self.lay_graph = QGridLayout()

        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.setStyleSheet("QStatusBar::item{ border: 0px solid black };")
        self.statusBar_msg = ""
        
        self.myMessage = QLabel()
        self.myMessage.setText(self.statusBar_msg)
        self.statusBar.addWidget(self.myMessage)

        self.lay_cb = QHBoxLayout()
        
        self.bus_voltage = QComboBox()
        self.bus_voltage.addItems( sensor.bus_voltage_ranges.keys() )
        self.bus_voltage.currentIndexChanged.connect(self.changed_config)    

        self.gain = QComboBox()
        self.gain.addItems( sensor.gain_ranges.keys() )
        self.gain.currentIndexChanged.connect(self.changed_config)    

        self.badcres = QComboBox()
        self.badcres.addItems( sensor.badcres_ranges.keys() )
        self.badcres.currentIndexChanged.connect(self.changed_config)    

        self.sadcres = QComboBox()
        self.sadcres.addItems( sensor.sadcres_ranges.keys() )
        self.sadcres.currentIndexChanged.connect(self.changed_config)            
       
        self.mode = QComboBox()
        self.mode.addItems( sensor.mode_ranges.keys() )
        self.mode.currentIndexChanged.connect(self.changed_config)     

        self.bus_voltage.setCurrentText("BUS_VOLTAGE_RANGE_32V")
        self.gain.setCurrentText("GAIN_1_40MV")        
        self.badcres.setCurrentText("BUS_VOLTAGE_ADC_RES_12BIT")
        self.sadcres.setCurrentText("SHUNT_ADC_RES_12BIT_1S_532US")		
        self.mode.setCurrentText("SHUNT_AND_BUS_VOLTAGE_CONTINUOUS")		
   
        self.lay_cb.addWidget(self.bus_voltage)
        self.lay_cb.addWidget(self.gain)
        self.lay_cb.addWidget(self.badcres)
        self.lay_cb.addWidget(self.sadcres)
        self.lay_cb.addWidget(self.mode)
        self._lay.addLayout(self.lay_cb, 0, 0 )
        self._lay.addLayout(self.lay_graph, 1, 0 )
        
        self.showMaximized()
            
        self.timer = QTimer(self)
        self.timer.setSingleShot(False)
        self.timer.timeout.connect(self.process_samples)

        self.v = [0] * GRAPH_SAMPLES    
        self.v_graph = create_graph( "Voltage (V)" )
        self.v_label = QLabel(self)
        self.v_label.setFont(QtGui.QFont("Times", FONT_SIZE, QtGui.QFont.Bold))
        self.lay_graph.addWidget ( self.v_graph, 1, 1)
        self.lay_graph.addWidget ( self.v_label, 1, 2)
    
        self.c = [0] * GRAPH_SAMPLES
        self.c_graph = create_graph( "Current (A)" )
        self.c_label = QLabel(self)
        self.c_label.setFont(QtGui.QFont("Times", FONT_SIZE, QtGui.QFont.Bold))
        self.lay_graph.addWidget ( self.c_graph, 2, 1)   
        self.lay_graph.addWidget ( self.c_label, 2, 2)			

        self.p = [0] * GRAPH_SAMPLES
        self.p_graph = create_graph( "Power (W)" )
        self.p_label = QLabel(self)
        self.p_label.setFont(QtGui.QFont("Times", FONT_SIZE, QtGui.QFont.Bold))
        self.lay_graph.addWidget ( self.p_graph, 3, 1)   
        self.lay_graph.addWidget ( self.p_label, 3, 2)	
        
        sensor.config_options( self.bus_voltage.currentText(), self.gain.currentText(), self.badcres.currentText(), self.sadcres.currentText(), self.mode.currentText() )          
        
        if sensor.open(0) != -1:
            sensor.reset(0)
            sensor.setStream(0,1)
            sensor.calibration()
            time.sleep(0.01)
            sensor.configuration()
            time.sleep(0.01)
            self.timer.start(1)
        else:
            print("No hay comunicacion el dispositivo CH341")
            sys.exit(1)
    
    def process_samples(self):   
        voltage = sensor.get_bus_voltage()
        self.v.append(voltage)
        update_graph(self.v_graph, self.v, sensor.get_max_volts())
        self.v_label.setText( sensor.format(voltage, "V") + "\n" + sensor.format(sensor.get_max_volts(), "V") + " Max" )
        current = sensor.get_current()
        self.c.append(current)  
        update_graph(self.c_graph, self.c, sensor.get_max_amps())
        self.c_label.setText( sensor.format(current, "A") + "\n" + sensor.format(sensor.get_max_amps(), "A") + " Max" )
        power = sensor.get_power()
        self.p.append(power)  
        update_graph(self.p_graph, self.p, sensor.get_max_volts() * sensor.get_max_amps())
        self.p_label.setText( sensor.format(power, "W") )        
        self.timer.start(SAMPLING_TIME)         
    
    def changed_config(self,i):
        sensor.config_options( self.bus_voltage.currentText(), self.gain.currentText(), self.badcres.currentText(), self.sadcres.currentText(), self.mode.currentText() )
        sensor.stop(0)
        if sensor.open(0) != -1:
            sensor.reset(0)
            sensor.setStream(0, 1)
            sensor.calibration()
            time.sleep(0.01)
            sensor.configuration()
            time.sleep(0.01)	
               
        
if __name__ == '__main__':
    app = QApplication(sys.argv)
    project_name = "INA219 Current Sensor"
    ventana = MainWindow(project_name)
    ventana.show()
    sys.exit(app.exec_())
    