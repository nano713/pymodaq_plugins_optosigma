import pyvisa 
import time
import logging 
logger = logging.getLogger(__name__)


class AxisError(Exception): 
    MESSAGES = {
        "X" : "Command or parameter errors", 
        "K" : "Normal state", 
        "L" : "First-axis stopped at LS",
        "W" : "First and second axes stopped at LS", 
    }
    def __init__(self, error_code):
        self.message = self.MESSAGES[error_code]
class GRC:

    default_units = 'um'

    def __init__(self, rsrc_name):
        self._actuator = None
        self.rsrc_name = rsrc_name
        self.position = [None, None, None]
        self.speed = [None, None, None]

    
    def connect(self): 
        rm = pyvisa.ResourceManager()
        self._actuator = rm.open_resource(self.rsrc_name) # Connect to the actuator
        self._actuator.write_termination = "\r\n"
        self._actuator.read_termination = "\r\n"
        self._actuator.baud_rate = 9600
        logger.info(f"Connection to {self._actuator} successful")
    

    def move(self, position, channel): 
        """Move the specified channel to the position."""
        if position >= 0:
            self._actuator.write(f"A:{channel}+P{position}")
            logger.info(f"Moving {channel} to {position}")
        else:
            self._actuator.write(f"A:{channel}-P{abs(position)}")
            logger.info(f"Moving {channel} to {position}")
        self._actuator.write("G:")
        self.position[channel-1] = position
    
    def move_rel(self, position, channel):
        """Move the specified channel to the relative position."""  
        if position >= 0:
            self._actuator.write(f"M:{channel}+P{position}")
            logger.info(f"Moving {channel} to {position}")
        else: 
            self._actuator.write(f"M:{channel}-P{abs(position)}")
            logger.info(f"Moving {channel} to {position}")
        self._actuator.write("G:")
        self.wait_for_ready(channel)
        self.position[channel-1] = position

    def stop(self, channel): 
        """Stop the specified channel."""
        self._actuator.write(f"L:{channel}")
    

    def get_position(self, channel): 
        """Get the position of the specified channel."""
        return self.position[channel-1]
    
    def home(self, channel): 
        """Move the specified channel to the home position."""
        self._actuator.write(f"H:{channel}")
        logger.info(f"Homing {channel}")

    def set_speed(self, speed_min,speed_fin, accel_t, channel): 
        """Set the speed of the specified channel"""
        if speed_min >= 0 and speed_fin >= 0 and accel_t >= 0:
            speed = self._actuator.write(f"D:{channel}S{speed_min}F{speed_fin}R{accel_t}")
            self.speed[channel-1] = speed
        
    def get_speed(self, channel): 
        """Get the speed of the specified channel"""
        return self.speed[channel-1]
    
    def close(self): 
        pyvisa.ResourceManager().close()
        
    def check_error(self):
        """Checks for the errors and returns the error message."""
        error = self._actuator.query("Q:")
        error = error.split(",")[2]
        if error != "K":
            logger.error(f"Error: {error}")
            AxisError(error)

    def read_state(self): 
        """Read the state of the specified channel."""
        state = self._actuator.write(f"!:")
        return state

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