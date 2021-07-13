from PyQt5 import QtWidgets, uic
from PyQt5.QtCore import QThread, QObject, pyqtSignal
import sys
import helpers
import csv
from datetime import datetime
import time

err= {}
read_err_occured = False
class Worker(QObject):

    finished = pyqtSignal()  # give worker class a finished signal

    def __init__(self, devices, device_addresses, registers, save_location, timeinterval, maxreading):
        super(Worker, self).__init__()
        self.save_location = save_location
        self.devices = devices
        self.device_addresses = device_addresses
        self.registers = registers        
        self.timeinterval = timeinterval
        self.maxreading = maxreading
        

    def logging(self):
        self.continue_logging = True
        # opens output file
        csvfile = open(self.save_location, 'w', newline='')
        csvwriter = csv.writer(csvfile, delimiter=',', quotechar='"')
        csvwriter.writerow(['Time Stamp', 'Address', 'Register', 'Value'])
        
        num_entries = 0
        file_num = 0
        
        while self.continue_logging:
            time_then = time.time()
            for address in self.device_addresses:
                for register in self.registers[address]:
                    time_now = time.time()
                    try:
                        reading = self.devices[address].read_register(register)
                        if True:
                            if reading > 65500:
                                reading = reading - 65535
                    except:
                        e = sys.exc_info()
                        reading = f"{e[0]}: {e[1]}"
                        global err
                        err[address][register] += 1
                        global read_err_occured
                        read_err_occured = True
                        
                    dt = datetime.fromtimestamp(time_now).strftime('%m/%d/%Y %H:%M:%S.%f')
                    entry = [dt, address, register, reading]
                    csvwriter.writerow(entry)
                    num_entries += 1
                    if num_entries == self.maxreading:
                        csvfile.close()
                        file_num += 1
                        file_name = self.save_location[:-4] + f"{file_num:03}" + ".csv"
                        csvfile = open(file_name, 'w', newline='')
                        csvwriter = csv.writer(csvfile, delimiter=',', quotechar='"')
                        csvwriter.writerow(['Time Stamp', 'Address', 'Register', 'Value'])
                        num_entries = 0
            while time.time()-time_then < self.timeinterval:
                continue
        
        # when logging stopped
        csvfile.close()

        self.devices[self.device_addresses[0]].serial.close()
        self.finished.emit()
    
    def stop_logging(self):
        self.continue_logging = False
        
class Ui(QtWidgets.QMainWindow):
    
    stop_signal = pyqtSignal()  # make a stop signal to communicate with the worker in another thread
    
    def __init__(self):
        super(Ui, self).__init__() # Call the inherited classes __init__ method
        uic.loadUi('gui.ui', self) # Load the .ui file
        
        self.show() # show window when obj created
        
        
        self.refresh_ports()
        self.portselection.currentTextChanged.connect(self.portselect)
        
        # creating handles for modbus reading data
        self.devices = {}
        self.device_addresses = []
        self.registers = {}
        self.port = ""
        
        self.save_location="./logs/log results.csv"
        self.filenamebox.setText(self.save_location)
        self.filenamebox.textChanged.connect(self.update_location)

        # disconnects devices before closing window
        quit = QtWidgets.QAction("Quit", self)
        quit.triggered.connect(self.exit_window)
        
        # refreshes available ports
        self.refreshport.clicked.connect(self.refresh_ports)
        
        # load json button reads json file, and assigns values to the reading parameters
        self.loadjson.clicked.connect(self.load_json)
        
        # opens a file browser to select save location
        self.filebrowse.clicked.connect(self.open_save_location)
        
        # Start Button action:
        self.startbutton.clicked.connect(self.start)

        # Stop Button action:
        self.stopbutton.clicked.connect(self.stop_thread)

        # Thread:
    def create_thread(self):
        self.thread = QThread()
        self.worker = Worker(self.devices, 
                             self.device_addresses, 
                             self.registers, 
                             self.save_location, 
                             self.timeinterval.value(),
                             self.maxreading.value())
        self.stop_signal.connect(self.worker.stop_logging)  # connect stop signal to worker stop method
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.logging)
        self.thread.finished.connect(self.worker.stop_logging)
        self.worker.finished.connect(self.thread.quit)  # connect the workers finished signal to stop thread
        self.worker.finished.connect(self.worker.deleteLater)  # connect the workers finished signal to clean up worker
        self.thread.finished.connect(self.thread.deleteLater)  # connect threads finished signal to clean up thread
        global read_err_occured
        read_err_occured = False
        
    def start(self):
        global err
        err = {address:{register:0 for register in self.registers[address]} for address in self.device_addresses}
        self.groupBox.setEnabled(False)
        self.startbutton.setEnabled(False)
        self.stopbutton.setEnabled(True)
        self.statusdisplay.append(f"logging started at {datetime.fromtimestamp(time.time()).strftime('%m/%d/%Y %H:%M:%S')}")
        self.create_thread()
        self.thread.start()
        
    # When stop_btn is clicked this runs. Terminates the worker and the thread.
    def stop_thread(self):
        self.stop_signal.emit()  # emit the finished signal on stop
        self.groupBox.setEnabled(True)
        self.stopbutton.setEnabled(False)
        self.startbutton.setEnabled(True)
        self.statusdisplay.append(f"logging stopped at {datetime.fromtimestamp(time.time()).strftime('%m/%d/%Y %H:%M:%S')}")
        if read_err_occured:
            self.statusdisplay.append("number of reading errors encountered:")
            self.statusdisplay.append(str(err))
        else:
            self.statusdisplay.append("no reading errors occured.")

    def exit_window(self, event):
        if self.devices:
            self.devices[self.device_addresses[0]].serial.close()
        self.close()
    
    def open_save_location(self):
        file_name, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Save as", filter="*.csv")
        self.filenamebox.setText(file_name)
    
    def update_location(self):
        inputtext = self.filenamebox.text()
        if inputtext:
            self.save_location = inputtext
        else:
            self.save_location="./logs/log results.csv"
            self.filenamebox.setText(self.save_location)
        
    def load_json(self):
        file_name, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Open JSON file", filter="*.json")
        try: # try to open json file, and error handling if screw up
        # assigns values to reading parameters
            self.device_addresses, self.registers = helpers.open_file(file_name)
        except:
            self.statusdisplay.append("Error opening JSON. Check JSON file formatting.")
            return
        self.statusdisplay.append(f"Loaded json: {file_name}")
        self.statusdisplay.append("Registers to read:")
        self.statusdisplay.append(str(self.registers))
        try: # creates connection to devices. 
            self.devices = helpers.open_devices(self.port, self.device_addresses)
        except:
            self.statusdisplay.append("Device connection failed. try refreshing ports, check json file/device connection")
        self.check_addresses()
            
    def portselect(self, txt):
        if txt:
            self.port = txt
            self.statusdisplay.append(f"Reading from port {self.port}")
        '''else:
            self.statusdisplay.append("No ports found")'''
            
    def refresh_ports(self):
        self.portselection.clear()
        ports = helpers.find_ports()
        if ports:
            for i in ports:
                self.portselection.addItem(i)
        self.statusdisplay.append("ports refreshed")
        if ports:
            self.portselect(ports[0])
    
    def check_addresses(self): # checks if addresses in JSON are valid. if so, enables start button
        temp = False
        slaveAddressRegister = 17697
        for address in self.device_addresses:
            try:
                assert address == self.devices[address].read_register(slaveAddressRegister)
                self.statusdisplay.append(f"Successfully connected to device {address}.")
                temp = True
            except:
                self.statusdisplay.append(f"Failed to connect to device {address}.")
        if temp:
            self.startbutton.setEnabled(True)
            self.statusdisplay.append("Ready to start.")
        else:
            self.startbutton.setEnabled(False)
            self.statusdisplay.append("Device connection failed. try refreshing ports, check json file/device connection")
            self.statusdisplay.append("Reload JSON to try again.")
        
#start ui when run
app = QtWidgets.QApplication(sys.argv)
window = Ui()
app.exec_()
