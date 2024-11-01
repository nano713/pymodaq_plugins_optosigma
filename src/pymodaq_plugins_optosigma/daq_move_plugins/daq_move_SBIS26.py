import logging
from pymodaq.control_modules.move_utility_classes import DAQ_Move_base, comon_parameters_fun, main, DataActuatorType,\
    DataActuator  # common set of parameters for all actuators
from pymodaq.utils.daq_utils import ThreadCommand # object used to send info back to the main thread
from pymodaq.utils.parameter import Parameter
from pymodaq_plugins_optosigma.hardware.Sbis26_VISADriver import SBIS26
logger = logging.getLogger(__name__)


# DK - Delete this class because we use the separate hardware code
class PythonWrapperOfYourInstrument:
    #  TODO Replace this fake class with the import of the real python wrapper of your instrument
    pass

# TODO:
# (1) change the name of the following class to DAQ_Move_TheNameOfYourChoice
# (2) change the name of this file to daq_move_TheNameOfYourChoice ("TheNameOfYourChoice" should be the SAME
#     for the class name and the file name.)
# (3) this file should then be put into the right folder, namely IN THE FOLDER OF THE PLUGIN YOU ARE DEVELOPING:
#     pymodaq_plugins_my_plugin/daq_move_plugins

rsrc_name = "" # DK - delete this line
# DK - if the class name is DAQ_Move_SBIS26, then the file name should be daq_move_SBIS26.py (the same case after the last underscore)
class DAQ_Move_SBIS26(DAQ_Move_base):
    """ Instrument plugin class for an actuator.
    
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
    
    is_multiaxes = True 
    _axis_names: Union[List[str], Dict[str, int]] = {"X": 1, "Y": 2, "Z": 3}
    _controller_units: Union[str, List[str]] = "um" # DK - replace with "". SBIS26 only has pulse unit.
    _epsilon: Union[float, List[float]] = (
        0.1  
    )
    data_actuator_type = (
        DataActuatorType.DataActuator
    ) 

    params = [
        {
            "title": "Serial Number:",
            "name": "serial_number",
            "type": "list",
            "limits": rsrc_name,
            "value": rsrc_name[0],
        },
        {
            "title": "Unit:",
            "name": "unit",
            "type": "list",
            "values": ["um", "mm", "nm", "deg", "pulse"],
            "value": "um",
        },
        {"title": "Speed:", "name": "speed_ini", "type": "float", "value": 0},
        {"title": "Acceleration:", "name": "accel_t", "type": "float", "value": 1},
        {"title": "Speed:", "name": "speed_fin", "type": "float", "value": 1.2},
    ] + comon_parameters_fun(is_multiaxes, axis_names=_axis_names, epsilon=_epsilon)

    def ini_attributes(self):
        #  TODO declare the type of the wrapper (and assign it to self.controller) you're going to use for easy
        #  autocompletion
        self.controller: SBIS26 = None

    # def get_actuator_value(self):
    #     """Get the current value from the hardware with scaling conversion.

    #     Returns
    #     -------
    #     float: The position obtained after scaling conversion.
    #     """
    #     ## TODO for your custom plugin
    #     raise NotImplemented  # when writing your own plugin remove this line
    #     pos = DataActuator(data=self.controller.your_method_to_get_the_actuator_value())  # when writing your own plugin replace this line
    #     pos = self.get_position_with_scaling(pos)
    #     return pos

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
           self.controller.set_speed(self.speed_ini, self.speed_fin, self.accel_t, self._axis_names)
           # AD: self.controller.set_speed(self.settings["speed_ini"], self.settings["speed_fin"], self.settings["accel_t"], self._axis_names)?
           # or is this old formatting that is no longer used? 
        elif param.name() == "unit":
            unit_dict = {"um": "U", "mm": "M", "nm": "N", "deg": "D", "pulse": "P"}
            self.stage.set_unit(unit_dict[self.settings["unit"]])
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
            self.controller = SBIS26(rsrc_name)
            self.controller.open_connection()
        else: 
            logger.warning("This plugin is not initialized")
        
        info = "SBIS26 is initialized"
        initialized = True
        return info, initialized

    def move_abs(self, value: DataActuator):
        """ Move the actuator to the absolute target defined by value

        Parameters
        ----------
        value: (float) value of the absolute target positioning
        """

        value = self.set_position_with_scaling(value)

        self.controller.move(value.value())
        self.emit_status(
            ThreadCommand("Update_Status", ["SBIS26 has moved to the target position"])
        )
    def move_rel(self, value: DataActuator):
        """ Move the actuator to the relative target actuator value defined by value

        Parameters
        ----------
        value: (float) value of the relative target positioning
        """
        self.current_position = self.controller.get_position(self._axis_names)
        value = self.check_bound(self.current_position + value) - self.current_position
        self.target_value = value + self.current_position
        value = self.set_position_relative_with_scaling(value)

        self.controller.move_relative(value.value())
        self.emit_status(ThreadCommand('Update_Status', ['SBIS26 has moved to the relative target position']))

    def move_home(self):
        """Call the reference method of the controller"""
        self.controller.home()
        self.emit_status(ThreadCommand('Update_Status', ['SBIS26 has moved to the home position']))

    def stop_motion(self):
        """Stop the actuator and emits move_done signal"""
        self.controller.stop()
        self.emit_status(ThreadCommand('Update_Status', ['SBIS26 has stopped moving']))

if __name__ == '__main__':
    main(__file__)
