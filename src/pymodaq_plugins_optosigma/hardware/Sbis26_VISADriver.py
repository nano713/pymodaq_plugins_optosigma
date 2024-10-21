# Purpose: Driver code for SBIS26. This script will move the OptoSigma stage.

import time
import numpy as np
import pyvisa
# from pymodaq_plugins_optosigma import config
from pymodaq.utils.logger import set_logger, get_module_name

logger = set_logger(get_module_name(__file__))


class SBIS26VISADRIVER:
    """VISA class driver for the OptoSigma stage SBIS26."""

    def __init__(self, rsrc_name):

        # kwargs.setdefault("read_termination", "\r\n")
        self._instr = None
        self.rsrc_name = rsrc_name
        # self.rsrc_list = self.rm.list_resources()
        # self.visa_address = None
        # self.initialize()

    def initialize(self):
        """Initializes the stage."""
        # self.ch_1 = config.CHANNELS[0] #sets the channels for the stage
        # self.ch_2 = config.CHANNELS[1]
        # self.ch_2 = config.CHANNELS[2]
        rm = pyvisa.ResourceManager()

        # self._stage = self.rm.open_resource(
        #     self.visa_address, "read_termination", "\r\n", baud_rate=38400
        # )
        self._stage = rm.open_resource(self.rsrc_name)
        self._stage.read_termination = "\r\n"
        self._stage.baud_rate = 38400
        self._stage.parity = pyvisa.constants .Parity.none
        self._stage.stop_bits = pyvisa.constants.StopBits.one

        # self.stage = self.connect_to_stage(self.visa_address)

    def connect_to_stage(self):
        """Connects to the stage."""

        number = self._stage.ask("CONNECT?")
        logger.info("Connect to stage {}".format(number))
        return self.read()

    def count_devices(self):
        """Counts the number of devices connected."""

        number = self._stage.ask("CONNECT?")
        return number

    def read(self):
        """Reads and returns the message from the stage."""

        msg = super().read()  # check for errors that have occured
        if msg[-1] == "NG":
            print("Error")
        return msg

    def get_position(self, channel):
        """Gets the position of the stage depending on the channel."""

        channel = channel
        position = self._stage.read("Q:D,{channel}")
        return position

    def move(self, position, channel):
        """Moves the stage to the specified position."""

        channel = channel
        pos_min = -134217728
        pos_max = 134217727
        if position >= pos_min and position <= pos_max:
            if position >= 0:
                self._stage.write("A:D,{channel}," + f"{position}")
            else:
                self._stage.write("A:D,{channel}," + f"{position}")
        else:
            if position >= 0:
                position = pos_max
                self._stage.write("A:D,{channel}," + f"{position}")
            else:
                position = pos_min
                self._stage.write("A:D,{channel}," + f"{position}")
        self.wait_for_ready()
        return self.read()

    def move_relative(self, pos, channel):
        """Moves the stage to the specified relative position."""

        pos_min = -134217728
        pos_max = 134217727
        channel = channel
        current_position = self.ask("Q:D,{channel}")
        get_position = current_position.split(",")
        position = int(get_position[2])
        target_pos = position - pos

        if target_pos >= pos_min and target_pos <= pos_max:
            if pos >= 0:
                self._stage.write("M:D,{channel}," + f"{pos}")
            else:
                self._stage.write("M:D,{channel}," + f"{pos}")
        else:
            if pos >= 0:
                pos = pos_max
                self._stage.write("A:D,{channel}," + f"{pos}")
            else:
                pos = pos_min
                self._stage.write("A:D,{channel}," + f"{pos}")
        self.wait_for_ready()
        return self.read()

    def set_speed(self, speed, range, acce, channel):
        """Sets the speed of the stage."""

        channel = channel
        if speed > 0 and range > 0 and acce > 0:
            self._stage.write("D:D,{channel}," + f"+{speed},{range},{acce}")
            return self.read()
        else:
            print("NG")

    def stop(self):
        """Stops the stage."""

        self._stage.write("LE:A")
        return self.read()

    def wait_for_ready(self):
        """Waits for the stage to be ready."""

        time0 = time()
        while self.status() != "R":
            print(self.status())
            time1 = time() - time0
            if time1 >= 60:
                logger.warning("Timeout")
                break
            time.sleep(0.2)

    def home(self, channel):
        """Sends the stage to the home positiom."""

        channel = channel
        self._stage.write("H:D,{channel}")
        print("Moved home")
        self.wait_for_ready()
        return self.read()


    def close(self):
        """Closes the stage."""

        self.stage.close()