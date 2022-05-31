import sys
from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import QMainWindow, QApplication, QTableWidgetItem
from mdek_tag_logger import Ui_MainWindow
from PyQt5.QtSerialPort import QSerialPort, QSerialPortInfo
from PyQt5.QtCore import QIODevice
import serial
import time
import logging

class ReadingThread(QtCore.QThread):
    def __init__(self, serialport, logfile):
        QtCore.QThread.__init__(self)
        self.serialport = serialport
        self.logfile = logfile
    def run(self):
        while 1:
            lep_bytes = self.serialport.read_until(b'\n')
            lep_str = lep_bytes.decode("utf-8")
            print(lep_str[:-2])
            data = str(time.time()) + ',' + lep_str[:-2]
            try:
                self.logfile.info(data)
            except:
                pass



class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        self.setupUi(self)

        self.serialport = []
        self.serialport_name = None
        self.refresh_ports()
        self.logfile = []
        self.reader = []

        self.pushButton_refresh.clicked.connect(self.refresh_ports)
        self.pushButton_connect.clicked.connect(self.connect)
        self.pushButton_start.clicked.connect(self.start)
        self.pushButton_stop.clicked.connect(self.stop)
        # self.comboBox_available_ports.currentIndexChanged.connect(self.change_port)

    def change_port(self, serial_portname):
        print(serial_portname)
        self.serialport_name = serial_portname
        print(self.comboBox_available_ports.currentText())

    def refresh_ports(self):
        self.comboBox_available_ports.clear()
        available_ports = QSerialPortInfo.availablePorts()
        serialports = [serialport.systemLocation() for serialport in available_ports]
        self.comboBox_available_ports.addItems(serialports)
        self.comboBox_available_ports.setCurrentText(self.serialport_name)

    def connect(self):
        serialport_name = self.comboBox_available_ports.currentText()
        self.serialport_name = serialport_name[4:]
        print(serialport_name[4:])
        with serial.Serial() as ser:
            ser.baudrate = 115200
            ser.port = self.serialport_name
            ser.open()
            ser.write(b'\r\r')
            print(ser.portstr)  # check which port was really used
            self.serialport = ser
            while 1:
                new_str = ser.read_until(b'\n')
                print(new_str)
                if new_str == b' Help      :  ? or help\r\n':
                    last_str = ser.read_until(b'\n')
                    print(last_str)
                    break


    def start(self):
        self.serialport.open()
        self.serialport.write(b'lec\n')
        lep_rec = self.serialport.read_until(b'\n')
        print(lep_rec)
        self.new_log_file()
        self.reader = ReadingThread(self.serialport, self.logfile)
        self.reader.start()

    def stop(self):
        self.serialport.write(b'lec\n')
        self.reader.terminate()
        self.serialport.close()

    def new_log_file(self):
        log_time = time.time()
        log_time_str = time.strftime("%d%m%Y%H%M%S", time.localtime(log_time))
        fileh = logging.FileHandler('logs/' + log_time_str + 'mdekraw.log', 'w')
        formatter = logging.Formatter('%(message)s')
        fileh.setFormatter(formatter)
        logger = logging.getLogger()  # root logger
        for hdlr in logger.handlers[:]:  # remove all old handlers
            logger.removeHandler(hdlr)
        logger.addHandler(fileh)  # set the new handler
        logger.setLevel(logging.INFO)
        self.logfile = logger


def main_application():
    app = QApplication(sys.argv)
    main = MainWindow()
    main.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main_application()