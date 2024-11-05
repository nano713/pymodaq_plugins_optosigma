
import pyvisa 
import time
logger = logging.getLogger(__name__)

class RMCVISADRIVER():
    """Class to communicate with the RMC Actuator"""

    default_units = ""

    def __init__(self, rsrc_name):
        self._actuator = None
        self.rsrc_name = rsrc_name
        self.unit = ""
        self.position = [None, None, None]
        self.speed_ini = [None, None, None]
        self.speed_fin = [None, None, None]
        self.accel_t = [None, None, None]
    

    def set_unit(self, unit):
        self.unit = unit
    
    def connect(self):
        try:
            rm = pyvisa.ResourceManager()
            self._actuator = rm.open_resource(self.rsrc_name)
            self._actuator.write_termination = "\r\n"
            self._actuator.read_termination = "\r\n"
            logger.info(f"Connection to {self._actuator} successful") 
        except Exception as e:
            logger.error(f"Error connecting to {self.rsrc_name}: {e}")
    
    def set_mode(self):
        self._actuator.write()
    def move(self, position, channel):
        """Move the actuator to the specified position on the given channel."""
        if position >= 0:
            self._actuator.write()
        else: 
            self._actuator.write()
        self._actuator.write("A:")
        self.wait_for_ready(channel)
        self.position[channel-1] = position


    def get_position(self, channel): 
        """Returns the position of the specified channel."""
        return self.position[channel-1]


    def move_relative(self, position, channel): 
        if position >= 0: 
            self._actuator.write(f"M:{channel}+{self.unit}{position}")
            logger.info(f"Moving {channel} to {position}{self.unit}")
        else:
            self._actuator.write(f"M:{channel}-{self.unit}{abs({position})}")
            logger.info(f"Moving {channel} to {position}{self.unit}")
        self._actuator.write("A:") #check if this is correct....
        
    

    def home(self, channel):
        self._actuator.write(f"H:{channel}")
    def wait_for_ready(self, channel):
        time0 = time.time()
        while self.read_state(channel) != "R":
            logger.info("State: " + self.read_state(channel))
            time1 = time.time() - time0
            if time1 >= 60:
                logger.warning("Timeout")
                self.check_error(channel)
                break
            time.sleep(0.2)
    
    def stop(self, channel): 
    
    def read_state(self, channel): 
    
    def close(self):
    



