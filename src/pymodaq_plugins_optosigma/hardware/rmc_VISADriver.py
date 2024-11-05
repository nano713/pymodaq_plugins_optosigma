
import pyvisa 
logger = logging.getLogger(__name__)

class RMCVISADRIVER():
    """Class to communicate with the RMC Actuator"""

    default_units = ""

    def __init__(self, rsrc_name):
        self._actuator = None
        self.rsrc_name = rsrc_name
        self.unit = ""
    

    def set_unit(self, unit):
        self.unit = unit
    
    def connect(self):
        rm = pyvisa.ResourceManager()
        self._actuator = rm.open_resource(self.rsrc_name)
        self._actuator.write_termination = "\r\n"
        self._actuator.read_termination = "\r\n"
        logger.info(f"Connection to {self._actuator} successful") 

    def move_rel(self, position, channel): 
        if position > 0: 
            self._actuator.write(f"M:{channel}+{self.unit}{position}")
        if position < 0:
            self._actuator.write(f"M:{channel}-{self.unit}abs({position})")
    

    def home(self, channel):
        self._actuator.write(f"H:{channel}")
    



