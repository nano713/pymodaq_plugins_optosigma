# Purpose: Driver code for SBIS26. This script will move the OptoSigma stage. 

import numpy as np
import pyvisa
# from pymodaq_plugins_optosigma import config
import time
from pymodaq.utils.logger import set_logger, get_module_name

logger = set_logger(get_module_name(__file__))


class SBIS26VISADriver():
    """ VISA class driver for the OptoSigma stage SBIS26. """

    def __init__(self):
        # self.rm = pyvisa.ResourceManager()
        # kwargs.setdefault('read_termination', '\r\n')
        self._stage = None
        # self.rsrc_list = rsrc_list
        # self.visa_address = None
        self.baud_rate = 38400
        self.max = 134217727
        self.min = -134217728
        # self.initialize()

    def connect(self, visa_address):
        # self.ch_1 = config.CHANNELS[0] #sets the channels for the stage
        # self.ch_2 = config.CHANNELS[1]
        # self.ch_2 = config.CHANNELS[2]
        # self.visa_address = 'ASRL/dev/ttyUSB0::INSTR'
        self._stage = self.rm.open_resource(visa_address)
        self._stage.read_termination = '\r\n'
        self._stage.baud_rate = self.baud_rate
        self._stage.parity = pyvisa.constants.Parity.none
        self._stage.stop_bits = pyvisa.constants.StopBits.one

        # 'read_termination',
        # '\r\n',
        # baud_rate = self.baud_rate

        # self.stage = self.connect_to_stage(self.visa_address)

        # Assign the initial device number
        self._stage.write("#CONNECT:")

    # def connect_to_stage(self):
    #     number = self._stage.ask("CONNECT?")
    #     logger.info('Connect to stage {}'.format(number))
    #     return self.read()
    #
    #     self._stage.write("#CONNECT:")
    #     return self._stage.read()

    def count_devices(self):
        """count the number of devices in int"""
        number = self._stage.ask("CONNECT?")
        return number

    # def read(self):
    #     msg = super().read()  # check for errors that have occured
    #     if msg[-1] == "NG":
    #         print("Error")
    #     return msg

    def get_position(self, channel):

        position = self._stage.read(f"Q:D,{channel}")
        return position

    def move_abs(self, position, channel):

        pos_min = -134217728
        pos_max = 134217727
        if position >= pos_min and position <= pos_max:
            if position >= 0:
                self._stage.write(f"A:D,{channel}," + f"{position}")
            else:
                self._stage.write(f"A:D,{channel}," + f"{position}")
        else:
            if position >= 0:
                position = pos_max
                self._stage.write(f"A:D,{channel}," + f"{position}")
            else:
                position = pos_min
                self._stage.write(f"A:D,{channel}," + f"{position}")
        self.wait_for_ready()
        # return self.read()

    # Let's follow Thorlabs BrushlessDCMotor
    # def move_relative(self, pos, channel):
    #     pos_min = -134217728
    #     pos_max = 134217727
    #     channel = channel
    #     current_position = self.ask(f"Q:D + {channel}")
    #     get_position = current_position.split(",")
    #     position = int(get_position[2])
    #     target_pos = position - pos
    #
    #     if target_pos >= pos_min and target_pos <= pos_max:
    #         if pos >= 0:
    #             self._stage.write(f"M:D,{channel}," + f"{pos}")
    #         else:
    #             self._stage.write(f"M:D,{channel}," + f"{pos}")
    #     else:
    #         if pos >= 0:
    #             pos = pos_max
    #             self._stage.write(f"A:D,{channel}," + f"{pos}")
    #         else:
    #             pos = pos_min
    #             self._stage.write(f"A:D,{channel}," + f"{pos}")
    #     self.wait_for_ready()
    #     return self.read()

    def set_speed(self, speed, range, acce, channel):
        # channel = channel
        if speed > 0 and range > 0 and acce > 0:
            self._stage.write(f"D:D,{channel}," + f"{speed},{range},{acce}")
            # return self.read()
        else:
            print("NG")

    def stop(self):
        self._stage.write("LE:A")
        # return self.read()

    def wait_for_ready(self):
        time0 = time()
        while self.status() != 'R':
            print(self.status())
            time1 = time() - time0
            if time1 >= 60:
                logger.warning("Timeout")
                break
            time.sleep(0.2)

    def home(self, channel):
        """ Sends the stage to the home position."""
        self._stage.write(f"H:D,{channel}")
        print("Moved home")
        self.wait_for_ready()
        # return self.read()

    # def move_stage(self, position):
    #     self.stage.write('1PA{}'.format(position))

    def close(self):
        self.stage.close()

    # def read(self):
    #     msg = super().read()
    #     if msg[-1] == "NG":
    #         print("Not OK")
    #     return msg
