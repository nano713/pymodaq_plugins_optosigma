import numpy as np
import time
import pyvisa as visa
from pymodaq_plugins_optosigma import config
from pymodaq.utils.logger import set_logger, get_module_name

logger = set_logger(get_module_name(__file__))

# DK - reuse this class that we wrote in pymeasure instruments. See an example: https://github.com/nano713/pymeasure/blob/dev/sbis26/pymeasure/instruments/newport/esp300.py
class AxisError(Exception):
    """
    Raised when a particular axis causes an error for OptoSigma SHRC-203.

    """

    MESSAGES = {
        '1': 'Normal (S1 to S10 and emergency stop has not occurred)',
        '3': 'Command error',
        '7': 'Scale error (S1)',
        'F': 'Disconnection error (S2)',
        '1F': 'Overflow error (S4)',
        '3F': 'Emergency stop',
        '7F': 'Hunting error (S3)',
        'FF': 'Limit error (S5)',
        '1FF': 'Counter overflow (S6)',
        '3FF': 'Auto config error',
        '7FF': '24V IO overload warning (W1)',
        'FFF': '24V terminal block overload warning (W2)',
        '1FFF': 'System error (S7)',
        '3FFF': 'Motor driver overheat warning (W3)',
        '7FFF': 'Motor driver overheat error (S10)',
        'FFFF': 'Out of in-position range   (after positioning is completed) (READY)',
        '1FFFF': 'Out of in-position range (During positioning operation) (BUSY)',
        '3FFFF': 'Logical origin return is in progress',
        '7FFFF': 'Mechanical origin return is in progress',
        'FFFFF': 'CW limit detection',
        '1FFFFF': 'CCW limit detection',
        '3FFFFF': 'CW software limit stop',
        '7FFFFF': 'CCW software limit stop',
        'FFFFFF': 'NEAR sensor detection',
        '1FFFFFF': 'ORG sensor detection',
    }

    def __init__(self, code):
        self.message = self.MESSAGES[code]

    def __str__(self):
        return f"OptoSigma SHRC-203 Error: {self.message}"

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

    def check_error(self, channel):
        """
        Check if there is an error in the specified channel.
        """
        error = self._instr.query(f"?:{channel}E") # DK - correct the command
        if error != "1":
            return AxisError(error)

    def open_connection(self):  # probably don't need this
        """
        Open the connection with the controller.
        """
        try:
            self._instr = visa.ResourceManager().open_resource(self.rsrc_name)
            self._instr.baud_rate = 9600
            self._instr.data_bits = 8
            self._instr.parity = visa.constants.Parity.none
            self._instr.write_termination = "\r\n"
            self._instr.read_termination = "\r\n"
            logger.info(f"Connection to {self._instr} successful")
        except Exception as e:
            logger.error(f"Error connecting to {self.rsrc_name}: {e}")

    def set_loop(self, loop, channel): # DK - the order of the attributes should be consistent across the methods.
        # Either channel-> others or others -> channel. e.g., the order in this method is inconsistent with move method
        """
        Open the loop of the specified channel.
        1: Open loop
        0: Close loop
        """

        self._instr.write(f":F{channel}:{loop}") 
        logger.info(f"Channel {channel} loop set to {loop}")

    def get_loop(self, channel):
        """
        Get the loop status of the specified channel."""
        loop = self._instr.query(f"?:F{channel}")
        logger.info(f"Channel {channel} loop status: {loop}")
        return loop

    def move(self, position, channel):  # recheck this method
        """
        Move the specified channel to the position.
        """
        if position >= 0:
            self._instr.write(f"A:{channel}:" + f"+P{position}")
        else:
            self._instr.write(f"A:{channel}:" + f"-P%{abs(position)}")
        self._instr.write("G:")
        self.wait_for_ready()
        # return self.read_state(channel) DK - Delete. This duplicates the information with wait_for_stop(). Delete the rest of the duplicated information

    def get_position(self, channel):
        # DK - write the command to get the position of the stage. Use query() method.
        # See the example in the SBIS26
        pass

    
    def set_speed(self, speed_ini, speed_fin, accel, channel):
        """Sets the speed of the stage.
        Args:
            speed_inital (int): Initial speed of the stage.
            speed_final (int): Final speed of the stage.
            accel (int): Acceleration time of the stage.
            channel (int): Channel of the stage.
        """
        
        self.speed_ini = speed_ini # DK - follow SBIS26. Write other variables

        if 0 < speed_ini < speed_fin and accel > 0: # DK - follow SBIS26.
            self._instr.write(f"D:{channel},{speed_ini},{speed_fin},{accel}")
        else:
            Exception("Invalid parameters")

    # DK - Implement the following methods
    def get_speed(self, channel):
        """Get the speed of the stage."""
        speed = self._instr.query(f"?:D{channel}")
        logger.info(f"Channel {channel} speed: {speed}")
        return speed

    def move_relative(self, position, channel):
        """Move the stage to a relative position."""
        if position >= 0:
            self._instr.write(
                f"M:{channel}" + f"+P{position}"
            )  
        else:
            self._instr.write(
                f"M:{channel}" + f"-P%{abs(position)}"
            )  
        self._instr.write("G:")
        self.wait_for_ready()
        return self.read_state(channel)

    def home(self, channel):
        """Move the stage to the home position."""
        self._instr.write(f"H:{channel}")
        return self.read_state(channel)

    
    def wait_for_ready(self, channel):
        """Wait for the stage to stop moving."""
        time0 = time.time()
        while self.read_state(channel) != "R":
            print(self.status()) # DK - make sure you delete print() at the end
            time1 = time.time() - time0
            if time1 >= 60:
                logger.warning("Timeout")
                break
            time.sleep(0.2)

    def stop(self, channel):
        """Stop the stage"""
        self._instr.write(f"L:{channel}")
        self.wait_for_ready(channel)
        return self.read_state(channel)

    def read_state(self, channel):
        """Read the state if the stage is moving or not.
        B: Busy
        R: Ready"""
        state = self._instr.query(f"!:{channel}S")
        return state

    def close(self):
        """Close the connection with the controller."""
        pass