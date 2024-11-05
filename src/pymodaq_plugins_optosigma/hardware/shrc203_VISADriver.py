import numpy as np
import time
import pyvisa
from pymodaq.utils.logger import set_logger, get_module_name

logger = set_logger(get_module_name(__file__))
#delete all logger.info

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
    default_units = 'um'

    def __init__(self, rsrc_name):
        """
        Initialize the communication with the controller.
        """
        self._instr = None
        self.rsrc_name = rsrc_name
        self.unit = None # DK - initialize unit
        # self.channel = {"X": 1, "Y": 2, "Z": 3}
        # self.channel = [1, 2, 3]
        self.loop = [None, None, None]# {"X": None, "Y": None, "Z": None
        self.position = [None, None, None]
        self.speed_ini = [None, None, None]
        self.speed_fin = [None, None, None]
        self.accel_t = [None, None, None]
        # self.position = {"X":None, "Y": None,"Z" :None}
        # self.speed_ini = {"X": None, "Y": None, "Z": None}
        # self.speed_fin = {"X": None, "Y": None, "Z": None}
        # self.accel_t = {"X": None, "Y": None, "Z": None}


    def set_unit(self, unit: str):
        """
        Set the unit of the controller.
        "N" nanometer designation
        "U" micrometer designation
        "M" mm designation
        "D" degree designation
        "P" Designation without unit (pulse
        """
        self.unit = unit

    def check_error(self, channel):
        """
        Check if there is an error in the specified channel.
        """

        # DK - add timeout with "elif"
        # DK - "U1,K,K,K,R", fake: "OK"
        while True:
            time
            error = self._instr.query(f"SRQ:{channel}S")
            error = error.split(",")[0]            
            if error[0] == self.unit[channel]:
                return error
            else:
                return AxisError(error)
    
    def open_connection(self): 
                                
        """
        Open the connection with the controller.
        """
        try:
            rm = pyvisa.ResourceManager()
            self._instr = rm.open_resource(self.rsrc_name)
            self._instr.baud_rate = 9600
            self._instr.data_bits = 8 
            self._instr.parity = pyvisa.constants.Parity.none 
            self._instr.write_termination = "\r\n" 
            self._instr.read_termination = "\r\n" 
            logger.info(f"Connection to {self._instr} successful")
        except Exception as e:
            logger.error(f"Error connecting to {self.rsrc_name}: {e}")
    
    def set_mode(self):
        self._instr.write("MODE:HOST")

    def set_loop(self, loop : dict, channel : int):
        """
        Open the loop of the specified channel.
        1: Open loop
        0: Close loop
        """
        self.loop[channel] = self._instr.write(f"?:F{channel}{loop}")

    def get_loop(self, channel):
        """
        Get the loop status of the specified channel."""
        return self.loop[channel-1] 

    def move(self, position, channel): 
        """
        Move the specified channel to the position.
        """
        if position >= 0:
            self._instr.write(f"A:{channel}+{self.unit}{position}") # DK - need "+" somewhere in the command? Check with the manual
            logger.info(f"Moving {channel} to {position}")
        else:
            self._instr.write(f"A:{channel}-{self.unit}{abs(position)}")
            logger.info(f"Moving {channel} to {position}")
        self._instr.write("G:")
        self.wait_for_ready()
        self.position[channel-1] = position
        # self.position[list(self.channel.keys())[channel-1]] = position


    def get_position(self, channel):
        return self.position[channel-1]

    
    def set_speed(self, speed_ini, speed_fin, accel_t, channel): 
        """Sets the speed of the stage.
        Args:
            speed_inital (int): Initial speed of the stage.
            speed_final (int): Final speed of the stage.
            accel_t(int): Acceleration time of the stage.
            channel (int): Channel of the stage.
        """

        if 0 < speed_ini < speed_fin and accel_t> 0:
            self._instr.write(f"D:{channel},{speed_ini},{speed_fin},{accel_t}")
        else:
            Exception("Invalid parameters")

    def get_speed(self, channel):
        """Get the speed of the stage."""
        self._instr.query(f"?:D{channel}")
        speed = self._instr.query(f"?:D{channel}")
        self.speed_ini = speed.split("S")[1].split("F")[0]
        self.speed_fin = speed.split("F")[1].split("R")[0]
        self.accel_t= speed.split("R")[1]
        return self.speed_ini[channel-1], self.speed_fin[channel-1], self.accel_t[channel-1]

    def move_relative(self, position, channel):
        """Move the stage to a relative position."""
        if position >= 0:
            self._instr.write(
                f"M:{channel}" + f"+{self.unit}{position}"
            )
            logger.info(f"Moving {channel} to {position}")  
        else:
            self._instr.write(
                f"M:{channel}" + f"-{self.unit}{abs(position)}"
            )  
            logger.info(f"Moving {channel} to {position}")
        self._instr.write("G:")
        self.wait_for_ready()

    def home(self, channel):
        """Move the stage to the home position."""
        self._instr.write(f"H:{channel}")
        self.wait_for_ready(self, f"{channel}")

    
    def wait_for_ready(self, channel):
        """Wait for the stage to stop moving."""
        time0 = time.time()
        while self.read_state(channel) != "R":
            print(self.read_state(channel)) # DK - make sure you delete print() at the end
            time1 = time.time() - time0
            if time1 >= 60:
                logger.warning("Timeout")
                self.check_error(channel)
                break
            time.sleep(0.2)

    def stop(self, channel):
        """Stop the stage"""
        self._instr.write(f"L:{channel}")
        self.wait_for_ready(channel)

    def read_state(self, channel):
        """Read the state if the stage is moving or not.
        B: Busy
        R: Ready"""
        state = self._instr.query(f"!:{channel}S") # DK - add while loop if possible.
        return state

    def close(self):
        """Close the connection with the controller."""
        pass