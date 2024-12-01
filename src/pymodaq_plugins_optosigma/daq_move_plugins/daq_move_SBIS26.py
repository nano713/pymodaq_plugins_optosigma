from typing import Union, List, Dict
import logging
from pymodaq.control_modules.move_utility_classes import DAQ_Move_base, comon_parameters_fun, main, DataActuatorType, \
    DataActuator
from pymodaq.utils.daq_utils import ThreadCommand
from pymodaq.utils.parameter import Parameter
from pymodaq_plugins_optosigma.hardware.sbis26_VISADriver import SBIS26VISADriver

logger = logging.getLogger(__name__)


class DAQ_Move_SBIS26(DAQ_Move_base):
    """ SBIS26 Driver Integrated Motorized Stage plugin class

    This object inherits all functionalities to communicate with PyMoDAQ’s DAQ_Move module through inheritance via
    DAQ_Move_base. It makes a bridge between the DAQ_Move module and the Python wrapper of a particular instrument.

    Attributes:
    -----------
    controller: object
        The particular object that allow the communication with the hardware, in general a python wrapper around the
         hardware library.

    """

    is_multiaxes = True
    _axis_names: Union[List[str], Dict[str, int]] = {"X": 1, "Y": 2, "Z": 3}
    _controller_units: Union[str, List[str]] = " "
    _epsilon: Union[float, List[float]] = (0.9)
    data_actuator_type = (DataActuatorType.DataActuator)

    params = [
                 {
                     "title": "Instrument Address",
                     "name": "visa_name",
                     "type": "str",
                     "value": "ASRL4::INSTR",
                 },
                 {"title": "Speed Initial:", "name": "speed_ini", "type": "float", "value": 1000},
                 {"title": "Acceleration Time:", "name": "accel_t", "type": "float", "value": 100},
                 {"title": "Speed Final:", "name": "speed_fin", "type": "float", "value": 1000},
             ] + comon_parameters_fun(is_multiaxes, axis_names=_axis_names, epsilon=_epsilon)

    def ini_attributes(self):
        self.controller: SBIS26VISADriver = None

    def get_actuator_value(self):
        """Get the current value from the hardware with scaling conversion.

        Returns
        -------
        float: The position obtained after scaling conversion.
        """

        pos = DataActuator(data=self.controller.get_position(self.axis_value))
        pos = self.get_position_with_scaling(pos)
        return pos

    def close(self):
        """Terminate the communication protocol"""
        self.controller.close()

    def commit_settings(self, param: Parameter):
        """Apply the consequences of a change of value in the detector settings

        Parameters
        ----------
        param: Parameter
            A given parameter (within detector_settings) whose value has been changed by the user
        """
        if param.name() == "speed_ini" or param.name() == "speed_fin" or param.name() == "accel_t":
            self.controller.set_speed(self.settings["speed_ini"], self.settings["speed_fin"], self.settings["accel_t"],
                                      self.axis_value)
        else:
            pass

    def ini_stage(self, controller=None):
        """Actuator communication initialization

        Parameters
        ----------
        controller: (object)
            custom object of a PyMoDAQ plugin (Slave case). None if only one actuator by controller (Master case)

        Returns
        -------
        info: str
        initialized: bool
            False if initialization failed otherwise True
        """

        self.ini_stage_init(slave_controller=controller)
        if self.is_master:
            self.controller = SBIS26VISADriver(self.settings["visa_name"])
            self.controller.connect()
        else:
            logger.error("This plugin is not initialized")

        info = "SBIS26 is initialized"
        initialized = True
        return info, initialized

    def move_abs(self, value: DataActuator):
        """ Move the actuator to the absolute target defined by value

        Parameters
        ----------
        value: (float) value of the absolute target positioning
        """
        value = self.check_bound(value)
        self.target_value = value

        value = self.set_position_with_scaling(value)

        self.controller.move(value.value(), self.axis_value)

    def move_rel(self, value: DataActuator):
        """ Move the actuator to the relative target actuator value defined by value

        Parameters
        ----------
        value: (float) value of the relative target positioning
        """
        value = self.check_bound(self.current_position + value) - self.current_position
        self.target_value = value + self.current_position
        value = self.set_position_relative_with_scaling(value)

        self.controller.move_relative(value.value(), self.axis_value)

    def move_home(self):
        """Call the reference method of the controller"""
        self.controller.home(self.axis_value)

    def stop_motion(self):
        """Stop the actuator and emits move_done signal"""
        self.controller.stop()
        self.emit_status(ThreadCommand('Update_Status', ['SBIS26 has stopped moving']))


if __name__ == '__main__':
    main(__file__)