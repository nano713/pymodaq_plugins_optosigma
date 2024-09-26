# Purpose: Driver code for SBIS26. This script will move the OptoSigma stage. 

import numpy as np
import pyvisa as visa
from pymodaq_plugins_optosigma import config
from pymodaq.utils.logger import set_logger, get_module_name
logger = set_logger(get_module_name(__file__))

class SBIS26VISADRIVER():
    """ VISA class driver for the OptoSigma stage SBIS26. """
    def __init__(self, baud_rate = 38400, **kwargs):
        kwargs.setdefault('read_termination', '\r\n')
        self._stage = None
        self.visa_address = None
        self.initialize()

    def initialize(self):
        self.ch_1 = config.CHANNELS[0] #sets the channels for the stage
        self.ch_2 = config.CHANNELS[1]
        self.ch_2 = config.CHANNELS[2]
        self.visa_address = 'ASRL/dev/ttyUSB0::INSTR'
        self.stage = self.connect_to_stage(self.visa_address)

    def connect_to_stage(self, visa_address):
        number = self._stage.ask("CONNECT?")
        logger.info('Connect to stage {}'.format(number))

        self._stage.write("#CONNECT:")
        return self._stage.read()
    def read(self):
        msg = super().read() #check for errors that have occured
        if msg[-1] == "NG":
            print("Error")
        return msg 
    def get_position(self): 
        position = self._stage.read("Q:D,{channel}")
        return position
    def home(self): 
        """ Sends the stage to the home positio."""
        self._stage.write("H:D,{channel}")
        self._

    def move_stage(self, position):
        self.stage.write('1PA{}'.format(position))

    def close(self):
        self.stage.close()