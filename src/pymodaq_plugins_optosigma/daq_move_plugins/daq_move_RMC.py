from typing import Union, List, Dict
from pymodaq.control_modules.move_utility_classes import DAQ_Move_base, comon_parameters_fun, main, DataActuatorType, \
    DataActuator
from pymodaq.utils.daq_utils import ThreadCommand
from pymodaq.utils.parameter import Parameter
from pymodaq_plugins_optosigma.hardware.rmc_VISADriver import RMCVISADriver
from pymodaq.utils import logger


class DAQ_Move_RMC(DAQ_Move_base):
    """ RMC-02C 2 Axis Controller plugin class
    
    This object inherits all functionalities to communicate with PyMoDAQ’s DAQ_Move module through inheritance via
    DAQ_Move_base. It makes a bridge between the DAQ_Move module and the Python wrapper of a particular instrument.

    Attributes:
    -----------
    controller: object
        The particular object that allow the communication with the hardware, in general a python wrapper around the
         hardware library.
         
    """
    is_multiaxes = True
    _axis_names: Union[List[str], Dict[str, int]] = {"X": 1, "Y": 2}
    _controller_units: Union[str, List[str]] = RMCVISADriver.default_units
    _epsilon: Union[float, List[float]] = 0.001
    data_actuator_type = DataActuatorType.DataActuator

    params = [
                 {"title": "Instrument Address", "name": "visa_name", "type": "str", "value": "ASRL7::INSTR"},
                 {"title": "Speed", "name": "speed", "type": "int", "value": 8}
             ] + comon_parameters_fun(is_multiaxes, axis_names=_axis_names, epsilon=_epsilon)

    def ini_attributes(self):
        self.controller: RMCVISADriver = None

    def get_actuator_value(self):
        """Get the current value from the hardware with scaling conversion.

        Returns
        -------
        float: The position obtained after scaling conversion.
        """
        pos = DataActuator(
            data=self.controller.get_position(self.axis_value),
            unit=self._controller_units)
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

        if param.name() == 'speed':
            self.controller.set_speed(self.settings["speed"], self.axis_value)
        else:
            pass

    def set_initial_conditions(self):
        speed = 8
        channels = [1, 2]
        for channel in channels:
            self.controller.set_speed(speed, channel)
            self.controller.home(channel)

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
            self.controller = RMCVISADriver(self.settings["visa_name"])
            self.controller.connect()

        info = "RMC Actuator initialized"
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

        self.controller.move(int(value.value()), self.axis_value)

    def move_rel(self, value: DataActuator):
        """ Move the actuator to the relative target actuator value defined by value

        Parameters
        ----------
        value: (float) value of the relative target positioning
        """
        value = self.check_bound(self.current_position + value) - self.current_position
        self.target_value = value + self.current_position
        value = self.set_position_relative_with_scaling(value)

        self.controller.move_relative(int(value.value()), self.axis_value)

    def move_home(self):
        """Call the reference method of the controller"""

        self.controller.home(self.axis_value)
    def stop_motion(self):
        """Stop the actuator and emits move_done signal"""

        self.controller.stop(self.axis_value)

if __name__ == '__main__':
    main(__file__)