import numpy as np
import time
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
            # self._instr.write                need to check this command to connect
            logger.info(f"Connection to {self.instr} successful")
        except Exception as e:
            logger.error(f"Error connecting to {self.rsrc_name}: {e}")

    def set_loop(self, channel, loop):
        """
        Open the loop of the specified channel.
        1: Open loop
        0: Close loop
        """

        self._instr.write(f":F{channel}:" + f"{loop}")
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
        self.wait_for_stop()
        return self.read_state(channel)

    def set_speed(self, speed_inital, speed_final, accel, channel):
        """Sets the speed of the stage.
        Args:
            speed_inital (int): Initial speed of the stage.
            speed_final (int): Final speed of the stage.
            accel (int): Acceleration time of the stage.
            channel (int): Channel of the stage.
        """
        if 0 < speed_inital < speed_final and accel > 0:
            self._instr.write(f"D:{channel},{speed_inital},{speed_final},{accel}")
        else:
            Exception("Invalid parameters")

    def move_relative(self, position, speed, channel):
        """Move the stage to a relative position."""
        if position >= 0:
            self._instr.write(
                f"M:{channel}" + f"+P{position}"
            )  # check this command. Speed should be incorporated
        else:
            self._instr.write(
                f"M:{channel}" + f"-P%{abs(position)}"
            )  # check this command. Speed should be incorporated
        self._instr.write("G:")
        self.wait_for_stop()
        return self.read_state(channel)

    def home(self, channel):
        """Move the stage to the home position."""
        self._instr.write(f"H:{channel}")
        return self.read_state(channel)

    def wait_for_stop(self, channel):
        """Wait for the stage to stop moving."""
        time0 = time.time()
        while self.read_state(channel) != "R":
            print(self.status())
            time1 = time.time() - time0
            if time1 >= 60:
                logger.warning("Timeout")
                break
            time.sleep(0.2)

    def stop(self, channel):
        """Stop the stage"""
        self._instr.write(f"L:{channel}")
        self.wait_for_stop(channel)
        return self.read_state(channel)

    def read_state(self, channel):
        """Read the state if the stage is moving or not.
        B: Busy
        R: Ready"""
        state = self._instr.query(f"!:{channel}S")
        return state
