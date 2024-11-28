from typing import Union, List, Dict

from pymodaq.control_modules.move_utility_classes import (DAQ_Move_base, comon_parameters_fun, main, DataActuatorType, DataActuator,) 
from pymodaq.utils.daq_utils import (ThreadCommand) 
from pymodaq.utils.parameter import Parameter
from pymodaq_plugins_optosigma.hardware.shrc203_VISADriver import ( SHRC203VISADriver as SHRC203)
from pymodaq.utils.logger import set_logger, get_module_name

logger = set_logger(get_module_name(__file__))

class DAQ_Move_SHRC203(DAQ_Move_base):
    """SHRC203 3 Axis Stage Controller plugin class

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
    _controller_units: Union[str, List[str]] = SHRC203.default_units 
    _epsilon: Union[float, List[float]] = (0.1)
    data_actuator_type = (DataActuatorType.DataActuator) 

    params = [
        {
            "title": "Instrument Address:",
            "name": "visa_name",
            "type": "str",
            "value": "ASRL3::INSTR",
        },
        {
            "title": "Unit:",
            "name": "unit",
            "type": "list",
            "limits": ["um", "mm", "nm", "deg", "pulse"], 
            "value": "um",
        },
        {"title": "Loop:", "name": "loop", "type": "int", "value": 0},
        {"title": "Speed Initial:", "name": "speed_ini", "type": "float", "value": 0},
        {"title": "Acceleration Time:", "name": "accel_t", "type": "float", "value": 1},
        {"title": "Speed Final:", "name": "speed_fin", "type": "float", "value": 1.2},
    ] + comon_parameters_fun(is_multiaxes, axis_names=_axis_names, epsilon=_epsilon)

    def ini_attributes(self):
        self.stage: SHRC203 = None 

    def get_actuator_value(self):
        """Get the current value from the hardware with scaling conversion.

        Returns
        -------
        float: The position obtained after scaling conversion.
        """
        pos = DataActuator(
            data=self.stage.get_position(self.axis_value) 
        ) 
        pos = self.get_position_with_scaling(pos)
        return pos

    def close(self):
        """Terminate the communication protocol"""
        return self.stage.close()

    def commit_settings(self, param: Parameter):
        """Apply the consequences of a change of value in the detector settings

        Parameters
        ----------
        param: Parameter
            A given parameter (within detector_settings) whose value has been changed by the user
        """
        if (param.name() == "speed_ini" or param.name() == "speed_fin" or param.name() == "accel_t"):
            self.stage.set_speed(
                self.speed_ini, self.speed_fin, self.accel_t, self.axis_value
            )

        elif param.name() == "loop":
            self.stage.set_loop()
        elif param.name() == "unit":
            unit_dict = {"um": "U", "mm": "M", "nm": "N", "deg": "D", "pulse": "P"}
            self.stage.set_unit(unit_dict[self.settings["unit"]])
            self._controller_units = self.settings["unit"] 
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
        self.ini_stage_init(
            slave_controller=self.stage
        ) 

        if self.is_master:
            self.stage = SHRC203(self.settings["visa_name"]) 
            self.stage.open_connection()
        else:
            logger.warning("No controller has been defined. Please define one")

        info = "SHRC203 is Initialized" 
        self.stage.set_mode()
        initialized = True
        return info, initialized

    def move_abs(self, value: DataActuator): 
        """Move the actuator to the absolute target defined by value

        Parameters
        ----------
        value: (float) value of the absolute target positioning
        """

        value = self.set_position_with_scaling(value)

        self.stage.move(value.value(), self.axis_value) 

    def move_rel(self, value: DataActuator):
        """Move the actuator to the relative target actuator value defined by value

        Parameters
        ----------
        value: (float) value of the relative target positioning
        """
        value = self.check_bound(self.current_position + value) - self.current_position
        self.target_value = value + self.current_position
        value = self.set_position_relative_with_scaling(value)

        self.stage.move_relative(value.value(), self.axis_value)
        
    def move_home(self):
        """Call the reference method of the controller"""
        self.stage.home(self.axis_value)
       

    def stop_motion(self):
        """Stop the actuator and emits move_done signal"""
        self.stage.stop(self.axis_value)
        self.emit_status(ThreadCommand("Update_Status", ["Instrument stopped"])) 

    if __name__ == "__main__":
        main(__file__)