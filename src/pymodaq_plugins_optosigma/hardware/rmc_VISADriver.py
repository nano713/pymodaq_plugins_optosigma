import pyvisa
import time
import logging

logger = logging.getLogger(__name__)

class AxisError(Exception):
    MESSAGES = {
        "K": "Normal state",
        "A": "Other",
        "O": "Overflow"
    }

    def __init__(self, error_code):
        self.message = self.MESSAGES[error_code]

class RMCVISADriver:
    """Class to communicate with the RMC Actuator"""

    default_units = "um"

    def __init__(self, rsrc_name):
        self._actuator = None
        self.rsrc_name = rsrc_name
        self.position = [-1, -1]
        self.speed = [-1, -1]

    def check_error(self):
        """Check for errors."""
        error = self._actuator.query("Q:")
        error = error.split(",")[2]
        if error != "K":
            logger.error(f"Error: {error}")
            AxisError(error)

    def set_speed(self, speed, channel):
        """Set the speed of the specified channel."""
        if 0 < speed <= 8:
            speed = self._actuator.write(f"D:{channel}J{speed}")
            self.speed[channel - 1] = speed
        else:
            Exception("Invalid speed values")

    def get_speed(self, channel):
        """Returns the speed of the specified channel."""
        if self.speed[channel - 1] is None:
            return logger.error("Speed is None")
        return self.speed[channel - 1]

    def connect(self):
        """Connect to the actuator."""
        try:
            rm = pyvisa.ResourceManager()
            self._actuator = rm.open_resource(self.rsrc_name)
            self._actuator.write_termination = "\r\n"
            self._actuator.read_termination = "\r\n"
        except Exception as e:
            logger.error(f"Error connecting to {self.rsrc_name}: {e}")

    def set_mode(self):
        """Set the actuator to remote mode."""
        self._actuator.write("P:1")

    def move(self, position, channel):
        """Move the actuator to the specified position on the given channel.
        Parameters
        ----------
        position: int
            The position to move to.
        channel: int
            The channel to move.

        """
        # self.wait_for_ready(channel)
        if position >= 0:
            self._actuator.write(f"A:{channel}+U{position}")

        else:
            self._actuator.write(f"A:{channel}-U{abs(position)}")
        self._actuator.write("G:")
        # self.wait_for_ready(channel)
        self.position[channel - 1] = position

    def get_position(self, channel):
        """Returns the position of the specified channel."""
        if self.position[channel - 1] is None:
            return logger.error("Position is None")
        return self.position[channel - 1]

    def move_relative(self, position, channel):
        """Move the specified channel to the relative position."""
        # self.wait_for_ready(channel)
        if position >= 0:
            self._actuator.write(f"M:{channel}+U{position}")
        else:
            self._actuator.write(f"M:{channel}-U{abs(position)}")
        self._actuator.write("G:")
        # self.wait_for_ready(channel)
        self.position[channel - 1] = position + self.position[channel - 1]

    def home(self, channel):
        """Move the specified channel to the home position"""
        # self.wait_for_ready(channel)
        self._actuator.write(f"H:{channel}")
        # self.wait_for_ready(channel)
        self.position[channel - 1] = 0

    def wait_for_ready(self, channel):
        """Wait for the actuator to be ready."""
        time0 = time.time()
        while self.read_state(channel) != "R":
            time1 = time.time() - time0
            if time1 >= 60:
                logger.error("Timeout")
                self.check_error()
                break
            time.sleep(0.2)

    def stop(self, channel):
        """Stop the actuator on the specified channel."""
        self._actuator.write(f"L:{channel}")
        # self.wait_for_ready(channel)

    def read_state(self, channel):
        """Returns the state of the specified channel."""
        state = self._actuator.query("!:")
        state = state.split(",")[channel - 1]
        return state

    def close(self):
        """Closes the connection to the actuator."""
        pyvisa.ResourceManager().close()