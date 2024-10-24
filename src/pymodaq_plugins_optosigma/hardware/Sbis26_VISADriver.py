# Purpose: Driver code for SBIS26. This script will move the OptoSigma stage.

import time
import numpy as np
import pyvisa
# from pymodaq_plugins_optosigma import config
from pymodaq.utils.logger import set_logger, get_module_name

logger = set_logger(get_module_name(__file__))

class SBIS26VISADriver:
    """VISA class driver for the OptoSigma stage SBIS26."""

    def __init__(self, rsrc_name):

        # kwargs.setdefault("read_termination", "\r\n")
        self._instr = None
        self.rsrc_name = rsrc_name
        # self.rsrc_list = self.rm.list_resources() # DK: Delete. Defined in initialize method
        # self.visa_address = None # DK: Delete. Not used.
        self.baud_rate = 38400
        # self.max_position = 134217727 # DK: max is built in variable. Avoid hardcoding.
        # self.min_position = -134217728
        # self.initialize()

    def connect(self):
        """Initializes the stage."""
        # self.ch_1 = config.CHANNELS[0] #sets the channels for the stage # DK: Delete. Config is wrong.
        # self.ch_2 = config.CHANNELS[1] # DK: Delete.
        # self.ch_2 = config.CHANNELS[2] # DK: Delete.
        rm = pyvisa.ResourceManager()

        # self._stage = self.rm.open_resource( # DK: this style is wrong. Delete.
        #     self.visa_address, "read_termination", "\r\n", baud_rate=38400
        # )
        self._stage = rm.open_resource(self.rsrc_name)
        self._stage.read_termination = "\r\n"
        self._stage.baud_rate = self.baud_rate
        self._stage.parity = pyvisa.constants.Parity.none
        self._stage.stop_bits = pyvisa.constants.StopBits.one

        self._stage.write("#CONNECT")

        # self.stage = self.connect_to_stage(self.visa_address)  # DK: Delete.

    # def connect_to_stage(self):
    #     """Counts the number of stages connected."""  # DK/SG: Delete this. duplicated with count_devices.
    #
    #     number = self._stage.read("CONNECT?")
    #     logger.info("Connect to stage {}".format(number))
    #     return self.read()

    def count_devices(self):
        """Counts the number of devices connected."""

        number = self._stage.read("CONNECT?")
        logger.info(f"Connected to {number} stage(s)")
        return number

    def get_device_info(self):
        """Gets the device information.
        Returns (str): Information of the device.
        """

        info = self._stage.read("*IDN?")
        return info

    def status(self, channel):
        """Gets the status of the stage.
        Returns (str): Status of the stage.
        """

        status = {"C": "Stopped by clockwise limit sensor detected.",
                  "W": "Stopped by counterclockwise limit sensor detected.",
                  "E": "Stopped by both of limit sensor.",
                  "K": "Normal"}

        status_str = self._stage.read(f"Q:S,{channel}")
        key = status_str.split(",")[3]
        return status[key]

    # def read(self):
    #     """Reads and returns the message from the stage.
    #     Returns (str): Message from the stage.
    #     """
    #
    #     msg = super().read()  # check for errors that have occured # DK: do not use super() because SBIS26VISADRIVER does not use any inheritance.
    #     if msg[-1] == "NG":
    #         print("Error")
    #     return msg

    def get_position(self, channel):
        """Gets the position of the stage.
        Args:
            channel (int): Channel of the stage.
        Returns (int): Position of the stage.
        """

        position_str = self._stage.read(f"Q:D,{channel}")
        position = position_str.split(",")[2]
        return position

    def move(self, position, channel):
        """Moves the stage to the specified position.
        Args:
            position (int): Position to move the stage to.
            channel (int): Channel of the stage.

         """
        self._stage.write(f"A:D,{channel},{position}")
        self.wait_for_ready()

        # # pos_min = -134217728 # DK: Delete this. Use max_position and min_position defined above.
        # # pos_max = 134217727 # DK: Delete this. Use max_position and min_position defined above
        # if position >= pos_min and position <= self.max_position: # DK/SG: I prefer to rely on this in GUI as designed in PyMoDAQ
        #     if position >= 0:
        #         self._stage.write(f"A:D,{channel}," + f"{position}") # DK: use format like f"A:D,{channel}," + f"{position}". Same below.
        #     else:
        #         self._stage.write(f"A:D,{channel}," + f"{position}") #DK: format
        # else:
        #     if position >= 0:
        #         position = self.max_position
        #         self._stage.write(f"A:D,{channel}," + f"{position}") #DK: format
        #     else:
        #         position = pos_min
        #         self._stage.write(f"A:D,{channel}," + f"{position}") #DK: format
        # self.wait_for_ready()
        # return self.read()

    def move_relative(self, position, channel):
        """Moves the stage to the specified relative position.
        Args:
            pos (int): Relative position to move the stage to.
            channel (int): Channel of the stage.
        """

        self._stage.write(f"M:D,{channel},{position}")
        self.wait_for_ready()

        # # pos_min = -134217728 # DK: Delete this. Use max_position and min_position defined above
        # # self.max_position = 134217727 # DK: Delete this. Use max_position and min_position defined above
        # # channel = channel # DK: Delete this. Not needed.
        # current_position = self.read("Q:D,{channel}") #DK: format    w
        # get_position = current_position.split(",")
        # position = int(get_position[2])
        # target_pos = position - pos
        #
        # if target_pos >= pos_min and target_pos <= pos_max:
        #     if pos >= 0:
        #         self._stage.write(f"M:D,{channel}," + f"{pos}") #DK: format
        #     else:
        #         self._stage.write(f"M:D,{channel}," + f"{pos}") #DK: format
        # else:
        #     if pos >= 0:
        #         pos = pos_max
        #         self._stage.write(f"A:D,{channel}," + f"{pos}") #DK: format
        #     else:
        #         pos = pos_min
        #         self._stage.write(f"A:D,{channel}," + f"{pos}") #DK: format
        # self.wait_for_ready()
        # return self.read()

    def set_speed(self, speed_ini, speed_fin, accel_t, channel):
        """Sets the speed of the stage.
        Args:
            speed_ini (int): Initial speed of the stage.
            speed_fin (int): Final speed of the stage.
            accel_t (int): Acceleration time of the stage.
            channel (int): Channel of the stage.
        """
        if speed_ini > 0 and speed_fin > speed_ini and accel_t > 0:
            self._stage.write(f"D:D,{channel},{speed_ini},{speed_fin},{accel_t}")  # DK: format
        else:
            logger.warning("Invalid parameters")
        # # channel = channel
        # if speed > 0 and range > 0 and acce > 0:
        #     self._stage.write(f"D:D,{channel}," + f"+{speed},{range},{acce}") #DK: format
        #     return self.read()
        # else:
        #     print("NG")

    def stop(self):
        """Stops the stage."""

        self._stage.write("LE:A")
        # return self.read()

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
        """ Sends the stage to the home position."""
        self._stage.write(f"H:D,{channel}")
        # print("Moved home")
        self.wait_for_ready()
        # return self.read()

    def close(self):
        """Closes the stage."""

        self.stage.close()  # DK: stage should be _stage
