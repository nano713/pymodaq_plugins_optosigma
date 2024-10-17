# Purpose: Driver code for SBIS26. This script will move the OptoSigma stage. 

import numpy as np
import pyvisa as visa
from pymodaq_plugins_optosigma import config
from pymodaq.utils.logger import set_logger, get_module_name
logger = set_logger(get_module_name(__file__))

class SBIS26VISADRIVER():
    """ VISA class driver for the OptoSigma stage SBIS26. """
    def __init__(self, baud_rate = 38400, **kwargs):
        self.rm = pyvisa.ResourceManager()
        kwargs.setdefault('read_termination', '\r\n')
        self._stage = None
        self.rsrc_list = rsrc_list 
        self.visa_address = None
        self.initialize()

    def initialize(self):
        self.ch_1 = config.CHANNELS[0] #sets the channels for the stage
        self.ch_2 = config.CHANNELS[1]
        self.ch_2 = config.CHANNELS[2]
        self.visa_address = 'ASRL/dev/ttyUSB0::INSTR'
        self._stage = self.rm.open_resource(self.visa_address, 
                                    'read_termination', '\r\n',
                                      baud_rate = 38400)
        self.stage = self.connect_to_stage(self.visa_address)

    def connect_to_stage(self, visa_address):
        number = self._stage.ask("CONNECT?")
        logger.info('Connect to stage {}'.format(number))

        self._stage.write("#CONNECT:")
        return self._stage.read()
    def count_devices(self):
        number = self._stage.ask("CONNECT?")
        return number
    
    def read(self):
        msg = super().read() #check for errors that have occured
        if msg[-1] == "NG":
            print("Error")
        return msg 
    
    def get_position(self): 
        position = self._stage.read("Q:D,{channel}")
        return position
    def move(self, position):
        pos_min = -134217728
        pos_max = 134217727
        if position >= pos_min and position <= pos_max: 
            if position >= 0:
                self._stage.write("A:D,{channel}," + f"{position}")
            else:
                self._stage.write("A:D,{channel}," + f"{position}")
        else: 
            if position >= 0:
                position = pos_max
                self._stage.write("A:D,{channel}," + f"{position}")
            else: 
                position = pos_min
                self._stage.write("A:D,{channel}," + f"{position}")
        self.wait_for_ready()
        return position
    def home(self): 
        """ Sends the stage to the home positio."""
        self._stage.write("H:D,{channel}")
        self._

    def move_stage(self, position):
        self.stage.write('1PA{}'.format(position))

    def close(self):
        self.stage.close()