import numpy as np
import pyvisa as visa
from pymodaq_plugins_optosigma import config
from pymodaq.utils.logger import set_logger, get_module_name
logger = set_logger(get_module_name(__file__))

class SHRC203VISADriver:
    """
    Class to handle the communication with the Optosigma SHRC203 controller using the VISA protocol.
    """
    # List the Optosigma instruments the user has configured from the .toml configuration file
    list_instruments = {}
    for instr in config["Optosigma", "SHRC2100"].keys():
        if "INSTRUMENT" in instr:
            list_instruments[instr] = config["Optosigma", "SHRC2100", instr, "rsrc_name"]
    logger.info("Configured instruments: {}".format(list(list_instruments.items())))

    def __init__(self, rsrc_name):
        """
        Initialize the communication with the controller.
        """
        self._instr = None
        self.rsrc_name = rsrc_name
        self.instr = ""
        self.configured_modules = {}
