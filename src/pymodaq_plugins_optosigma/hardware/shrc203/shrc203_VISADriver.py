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

    def init_hardware(self):
        """Initialize the selected VISA resource

        :param pyvisa_backend: Expects a pyvisa backend identifier or a path to the visa backend dll (ref. to pyvisa)
        :type pyvisa_backend: string
        """
        # Open connexion with instrument
        rm = visa.highlevel.ResourceManager()
        logger.info("Resources detected by pyvisa: {}".format(rm.list_resources(query='?*')))
        try:
            self._instr = rm.open_resource(self.rsrc_name,
                                           write_termination="\n",
                                           read_termination="\n",
                                           )
            self._instr.timeout = 10000
            # Check if the selected resource match the loaded configuration
            model = self.get_idn()[32:36]
            if "21" not in model:
                logger.warning("Driver designed to use Optosigma SHRC2100, not {} model. Problems may occur.".format(model))
            for instr in config["Optosigma", "SHRC2100"]:
                if type(config["Optosigma", "SHRC2100", instr]) == dict:
                    if self.rsrc_name in config["Optosigma", "SHRC2100", instr, "rsrc_name"]:
                        self.instr = instr
            logger.info("Instrument selected: {} ".format(config["Optosigma", "SHRC2100", self.instr, "rsrc_name"]))
            logger.info("Optosigma model : {}".format(config["Optosigma", "SHRC2100", self.instr, "model_name"]))
        except visa.errors.VisaIOError as err:
            logger.error(err)