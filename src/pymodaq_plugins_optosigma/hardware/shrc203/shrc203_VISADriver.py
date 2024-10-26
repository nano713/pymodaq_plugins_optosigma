import numpy as np
import pyvisa as visa
from pymodaq_plugins_optosigma import config
from pymodaq.utils.logger import set_logger, get_module_name
logger = set_logger(get_module_name(__file__))

class SHRC203VISADriver:
    """
    Class to handle the communication with the Optosigma SHRC203 controller using the VISA protocol.
    """
    
    def __init__(self, rsrc_name):
        """
        Initialize the communication with the controller.
        """
        self._instr = None
        self.rsrc_name = rsrc_name
        self.instr = ""
        self.configured_modules = {}
    
    def open_connection(self): #probably don't need this
        """
        Open the connection with the controller.
        """
        try:
            self._instr = visa.ResourceManager().open_resource(self.rsrc_name)
            self.instr = self._instr.query("*IDN?")
            logger.info(f"Connection to {self.instr} successful")
        except Exception as e:
            logger.error(f"Error connecting to {self.rsrc_name}: {e}")
    
    def set_loop(self,channel, loop):
        """
        Open the loop of the specified channel.
        1: Open loop
        0: Close loop
        """

        self._instr.write(f":F{channel}:" + f"{loop}")
        logger.info(f"Channel {channel} loop set to {loop}")
    def get_loop(self,channel): 
        """
        Get the loop status of the specified channel."""
        loop = self._instr.query(f"?:F{channel}")
        logger.info(f"Channel {channel} loop status: {loop}")
        return loop
    
    def move(self,position, channel):
        """
        Move the specified channel to the position. 
        """
        if position >= 0:
            self._instr.write(f"A:{channel}:" + f"+P{position}")
        else:
            self._instr.write(f"A:{channel}:" + f"-P%{abs(position)}")




        
