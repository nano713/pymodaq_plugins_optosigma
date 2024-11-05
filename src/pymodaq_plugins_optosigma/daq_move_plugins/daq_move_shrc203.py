from typing import Union, List, Dict

from pymodaq.control_modules.move_utility_classes import (
    DAQ_Move_base,
    comon_parameters_fun,
    main,
    DataActuatorType,
    DataActuator,
)  # common set of parameters for all actuators
from pymodaq.utils.daq_utils import (
    ThreadCommand,
)  # object used to send info back to the main thread
from pymodaq.utils.parameter import Parameter
from pymodaq_plugins_optosigma.hardware.shrc203_VISADriver import (
    SHRC203VISADriver as SHRC203,
)
from pymodaq.utils.logger import set_logger, get_module_name

logger = set_logger(get_module_name(__file__))

# DK - follow the naming convention. this file name should be daq_move_SHRC203. See
# https://pymodaq.cnrs.fr/en/4.4.x/developer_folder/instrument_plugins.html#naming-convention.


# The file name should be daq_move_SHRC203.py and the class name should be DAQ_Move_SHRC203 (consistent upper/lower case)
class DAQ_Move_SHRC203(DAQ_Move_base):
    """Instrument plugin class for an actuator.

    This object inherits all functionalities to communicate with PyMoDAQ’s DAQ_Move module through inheritance via
    DAQ_Move_base. It makes a bridge between the DAQ_Move module and the Python wrapper of a particular instrument.

    TODO Complete the docstring of your plugin with:
        * The set of controllers and actuators that should be compatible with this instrument plugin.
        * With which instrument and controller it has been tested.
        * The version of PyMoDAQ during the test.
        * The version of the operating system.
        * Installation instructions: what manufacturer’s drivers should be installed to make it run?

    Attributes:
    -----------
    controller: object
        The particular object that allow the communication with the hardware, in general a python wrapper around the
         hardware library.

    # TODO add your particular attributes here if any
    """

    # DK - add defaults_unit = "um" and daq_move will take this.

    is_multiaxes = True 
    _axis_names: Union[List[str], Dict[str, int]] = {"X": 1, "Y": 2, "Z": 3}
    # DK - It may be good to use 'm' unit to apply _controller_units feature. I am afraid that mm becomes kilo micrometers k um
    _controller_units: Union[str, List[str]] = SHRC203.default_units # DK - replace with SHRC203VISADriver.default_units to get the default unit
    _epsilon: Union[float, List[float]] = (
        0.1  # TODO replace this by a value that is correct depending on your controller
    )
    # TODO it could be a single float of a list of float (as much as the number of axes)
    # Leave this as it is.
    data_actuator_type = (
        DataActuatorType.DataActuator
    ) 

    params = [
        {
            "title": "Instrument Address:",
            "name": "visa_name",
            "type": "str",
            "value": "ASRL3::INSTR",# DK - Replace this with "ASRL3::INSTR" or "" (empty). "value" is used as an initial value. :
                                    # Make note value must be changed to the actual serial number of the device.
        },
        {
            "title": "Unit:",
            "name": "unit",
            "type": "list",
            "limits": ["um", "mm", "nm", "deg", "pulse"], # DK - replace 'values' with 'limits'
            "value": "um",
        },
        {"title": "Loop:", "name": "loop", "type": "int", "value": 0},# DK - 'value' should be  "" (empty)
        {"title": "Speed Initial:", "name": "speed_ini", "type": "float", "value": 0},# DK - value "" (empty)
        {"title": "Acceleration Time:", "name": "accel_t", "type": "float", "value": 1},# DK - value "" (empty). 'title' should be "Acceleration Time"
        {"title": "Speed Final:", "name": "speed_fin", "type": "float", "value": 1.2},# DK - value "" (empty)
    ] + comon_parameters_fun(is_multiaxes, axis_names=_axis_names, epsilon=_epsilon)

    def ini_attributes(self):
        self.stage: SHRC203 = None 
        # self.axis_value = None
        #self.speed_ini = None # DK - Delete
        #self.default_units = "um" # DK - replace with _controller_units to be consistent

    # DK data = self.controller.get_position(self.axis_value) See example in https://github.com/nano713/pymodaq_plugins_thorlabs/blob/dev/kpz_plugin/src/pymodaq_plugins_thorlabs/daq_move_plugins/daq_move_BrushlessDCMotor.py
    def get_actuator_value(self):
        """Get the current value from the hardware with scaling conversion.

        Returns
        -------
        float: The position obtained after scaling conversion.
        """
        pos = DataActuator(
            data=self.stage.get_position(self.axis_value) # DK - replace with self.axis_value
        )  # when writing your own plugin replace this line
        pos = self.get_position_with_scaling(pos)
        return pos

    # run close method
    def close(self):
        """Terminate the communication protocol"""
        return self.stage.close()

    # DK - To get the axis name, we should use `self.axis_value`
    def commit_settings(self, param: Parameter):
        """Apply the consequences of a change of value in the detector settings

        Parameters
        ----------
        param: Parameter
            A given parameter (within detector_settings) whose value has been changed by the user
        """
        # default_units = 'um' # default units for the stage
        if (
            param.name() == "speed_ini"
            or param.name() == "speed_fin"
            or param.name() == "accel_t"
        ):
            self.stage.set_speed(
                self.speed_ini, self.speed_fin, self.accel_t, self.axis_value
            )

        elif param.name() == "loop":
            self.stage.set_loop()
        elif param.name() == "unit":
            unit_dict = {"um": "U", "mm": "M", "nm": "N", "deg": "D", "pulse": "P"}
            self.stage.set_unit(unit_dict[self.settings["unit"]])
            self._controller_units = self.settings["unit"] # DK -add this line to update the unit in GUI
        else:
            pass

    # DK - run self.controller = SHRC203VISADriver(rsrc_name) if self.is_master = True
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
        )  # will be useful when controller is slave

        if self.is_master:
            self.stage = SHRC203(self.settings["visa_name"]) 
            self.stage.open_connection()
        else:
            logger.warning("No controller has been defined. Please define one")

        info = "SHRC203 is Initialized"  # DK - replace this line with the actual info
        self.stage.set_mode()
        initialized = True
        return info, initialized

    # DK - use move method
    def move_abs(self, value: DataActuator): # DK - add channel
        """Move the actuator to the absolute target defined by value

        Parameters
        ----------
        value: (float) value of the absolute target positioning
        """

        # value = self.check_bound(value)
        value = self.set_position_with_scaling(value)

        self.stage.move(value.value(), self.axis_value) # DK - Add channel attribute (=self.axis_value)
        # DK - delete emit_status because this will be recorded on the log file but we do not have to record every signle move.
        # self.emit_status(
        #     ThreadCommand("Update_Status", ["SHRC203 has moved to the target position"])
        # )

    # DK - use move_relative method
    def move_rel(self, value: DataActuator):
        """Move the actuator to the relative target actuator value defined by value

        Parameters
        ----------
        value: (float) value of the relative target positioning
        """
        self.current_position = self.stage.get_position(self.axis_value) # DK - replace with self.axis_value
        value = self.check_bound(self.current_position + value) - self.current_position
        self.target_value = value + self.current_position
        value = self.set_position_relative_with_scaling(value)

        self.stage.move_relative(value.value(), self.axis_value) # DK - Add channel attribute (=self.axis_value)
        # self.emit_status( # DK - delete
        #     ThreadCommand(
        #         "Update_Status", ["SHRC203 has moved to the relative target position"]
        #     )
        # )

    def move_home(self):
        """Call the reference method of the controller"""
        self.stage.home(self.axis_value) # DK - Add channel attribute (=self.axis_value)
        # self.emit_status( # DK - delete
        #     ThreadCommand("Update_Status", ["SHRC203 has moved to the home position"])
        # )

    def stop_motion(self):
        """Stop the actuator and emits move_done signal"""
        self.stage.stop(self.axis_value) # DK - Add channel attribute (=self.axis_value)
        self.emit_status(ThreadCommand("Update_Status", ["Instrument stopped"])) # DK this is okay to keep because stop does not often happen.

    if __name__ == "__main__":
        main(__file__)
