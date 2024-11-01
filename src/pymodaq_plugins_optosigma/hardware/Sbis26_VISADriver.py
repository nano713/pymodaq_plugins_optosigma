
import time
import pyvisa
from pymodaq.utils.logger import set_logger, get_module_name

logger = set_logger(get_module_name(__file__))


class SBIS26VISADriver:
    """VISA class driver for the OptoSigma stage SBIS26."""

    def __init__(self, rsrc_name):

        self._stage = None
        self.rsrc_name = rsrc_name
        self.unit = None # DK - delete. SBIS26 only has pulse unit
        self.speed_ini = {"X": None, "Y": None, "Z": None}
        self.speed_fin = {"X": None, "Y": None, "Z": None}
        self.accel_t = {"X": None, "Y": None, "Z": None}
        self.position = {"X": None, "Y": None, "Z": None}

    def connect(self):
        """Initializes the stage."""
        rm = pyvisa.ResourceManager()

        self._stage = rm.open_resource(self.rsrc_name)
        self._stage.baud_rate = 38400
        self._stage.write_termination = '\r\n'
        self._stage.read_termination = '\r\n'
        self._stage.write("#CONNECT")

    def check_error(self, channel):
        """Gets the status of the stage.
        Args:
            channel (int): Channel of the stage.
        Returns (str): Status of the stage.
        """
        status = {"C": "Stopped by clockwise limit sensor detected.",
                  "W": "Stopped by counterclockwise limit sensor detected.",
                  "E": "Stopped by both of limit sensor.",
                  "K": "Normal"}

        while True:
            self._stage.query(f"SRQ:D,{channel}")
            error_str = self._stage.query(f"SRQ:D,{channel}")
            key = error_str.split(",")[3]
            if error_str in status.keys():
                channel_val = int(error_str.split(",")[1])
                if channel_val == channel:
                    return error_str[key]
                else:
                    continue
            time.sleep(0.2)

    def status(self, channel):
        """Gets the status of the stage.
        Args:
            channel (int): Channel of the stage.
        Returns (str): Status of the stage.
        """
        self._stage.query(f"SRQ:D,{channel}") # DK - add while loop if possible
        status_str = self._stage.query(f"SRQ:D,{channel}")
        key = status_str.split(",")[-1]
        return status_str[key]
    def set_unit(self, unit : str):
        """
        Set the unit of the controller.
        "N" nanometer designation
        "U" micrometer designation
        "M" mm designation
        "D" degree designation
        "P" Designation without unit (pulse
        """
        self.unit = unit

    def get_position(self, channel):
        """Gets the position of the stage.
        Args:
            channel (int): Channel of the stage.
        Returns (float): Position of the stage.
        """
        return self.position[channel]

    def move(self, position, channel):
        """Moves the stage to the specified position.
        Args:
            position (int): Position to move the stage to.
            channel (int): Channel of the stage.

         """
        if position >= 0:
            self._stage.write(f"A:D,{channel},+{position}")
        else:
            self._stage.write(f"A:D,{channel},{position}")
        self.wait_for_ready()

    def move_relative(self, position, channel):
        """Moves the stage to the specified relative position.
        Args:
            position (int): Relative position to move the stage to.
            channel (int): Channel of the stage.
        """

        self._stage.write(f"M:D,{channel},{position}")
        self.wait_for_ready()

    def set_speed(self, speed_ini, speed_fin, accel_t):
        """Sets the speed of the stage.
        Args:
            speed_ini (int): Initial speed of the stage.
            speed_fin (int): Final speed of the stage.
            accel_t (int): Acceleration time of the stage.
            channel (int): Channel of the stage.
        """
        self.speed_ini = speed_ini
        self.speed_fin = speed_fin
        self.accel_t = accel_t
        if 0 < speed_ini < speed_fin and accel_t > 0:
            self._stage.write(f"D:A,{speed_ini},{speed_fin},{accel_t}")
        else:
            logger.warning("Invalid parameters")

    def get_speed(self, channel):
        """Gets the speed of the stage."""
        return self.speed_ini[channel], self.speed_fin[channel], self.accel_t[channel]

    def stop(self):
        """Stops the stage."""

        self._stage.write("LE:A")

    def wait_for_ready(self, channel):
        """Waits for the stage to be ready."""

        time0 = time.time()
        while self.status(channel) != "R":
            print(self.status()) # DK - logger.debut(self.status())
            time1 = time.time() - time0
            if time1 >= 60:
                logger.warning("Timeout")
                break
            time.sleep(0.2)

    def home(self, channel):
        """ Sends the stage to the home position."""
        self._stage.write(f"H:D,{channel}")
        self.wait_for_ready()

    def close(self):
        """Closes the stage."""
        self._stage.close()
