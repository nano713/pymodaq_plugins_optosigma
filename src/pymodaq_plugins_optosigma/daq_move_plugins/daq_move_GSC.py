from typing import Union, List, Dict

from pymodaq.control_modules.move_utility_classes import DAQ_Move_base, comon_parameters_fun, main, DataActuatorType,\
    DataActuator  # common set of parameters for all actuators
from pymodaq.utils.daq_utils import ThreadCommand # object used to send info back to the main thread
from pymodaq.utils.parameter import Parameter
from pymodaq_plugins_optosigma.hardware.gsc_VISADriver import Gsc_VISADriver as GSC


class PythonWrapperOfYourInstrument:
    #  TODO Replace this fake class with the import of the real python wrapper of your instrument
    pass

# TODO:
# (1) change the name of the following class to DAQ_Move_TheNameOfYourChoice
# (2) change the name of this file to daq_move_TheNameOfYourChoice ("TheNameOfYourChoice" should be the SAME
#     for the class name and the file name.)
# (3) this file should then be put into the right folder, namely IN THE FOLDER OF THE PLUGIN YOU ARE DEVELOPING:
#     pymodaq_plugins_my_plugin/daq_move_plugins
class DAQ_Move_GSC(DAQ_Move_base):
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
    is_multiaxes = True # TODO for your plugin set to True if this plugin is controlled for a multiaxis controller
    _axis_names: Union[List[str], Dict[str, int]] = {'X-Axis', "Y-Axis"}  # TODO for your plugin: complete the list
    _controller_units: Union[str, List[str]] = GSC.default_units  # TODO for your plugin: put the correct unit here, it could be
    # TODO  a single str (the same one is applied to all axes) or a list of str (as much as the number of axes)
    _epsilon: Union[float, List[float]] = 0.1  # TODO replace this by a value that is correct depending on your controller
    # TODO it could be a single float of a list of float (as much as the number of axes)
    data_actuator_type = DataActuatorType.DataActuator  # wether you use the new data style for actuator otherwise set this
    # as  DataActuatorType.float  (or entirely remove the line)

    params = [
        {"title": "Instrument Address", "name": "visa_name", "type": "str", "value": ""}, 
        {"title": "Speed_ini", "name": "speed_ini", "type": "float", "value": 0}
        {"title": "Speed_fin", "name": "speed_fin", "type": "float", "value": 300}
        {"title": "Acceleration time", "name": "acceleration_time", "type": "float", "value": 0.1}
                ] + comon_parameters_fun(is_multiaxes, axis_names=_axis_names, epsilon=_epsilon)
 
    def ini_attributes(self):
        self.controller: GSC = None

    def get_actuator_value(self):
        """Get the current value from the hardware with scaling conversion.

        Returns
        -------
        float: The position obtained after scaling conversion.
        """
        pos = DataActuator(data=self.controller.get_position())  # when writing your own plugin replace this line
        pos = self.get_position_with_scaling(pos)
        return pos

    def user_condition_to_reach_target(self) -> bool:
        """ Implement a condition for exiting the polling mechanism and specifying that the
        target value has been reached

       Returns
        -------
        bool: if True, PyMoDAQ considers the target value has been reached
        """
        #AD 
        # This method is similar to wait for ready. We could call this and return the wait_for_ready method
        # from the controller to make the code cleaner and easier to understand. We would just do a loop in here
        # and return true if the valeu has been reached. 
        return True

    def close(self):
        """Terminate the communication protocol"""
        self.controller.close(self.axis_value) 

    def commit_settings(self, param: Parameter):
        """Apply the consequences of a change of value in the detector settings

        Parameters
        ----------
        param: Parameter
            A given parameter (within detector_settings) whose value has been changed by the user

        raise NotImplementedError 
            if the parameter is not implemented
        """

        if param.name() == "speed_ini" or param.name() == "speed_fin" or param.name() == "acceleration_time":
           self.controller.set_speed(self.settings["speed_ini"], self.settings["speed_fin"], self.settings["acceleration_time"] self.axis_value)
        else:
            raise NotImplementedError(f"Parameter {param.name()} not implemented")

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
       
        self.ini_stage_init(slave_controller=controller)  # will be useful when controller is slave

        if self.is_master:  # is needed when controller is master
            self.controller = GSC(self.settings["visa_name"]) #  arguments for instantiation!)
            self.controller.connect()

        info = "For once it actually worked....GSC Actuator initialized"
        initialized = True  # todo
        return info, initialized

    def move_abs(self, value: DataActuator):
        """ Move the actuator to the absolute target defined by value

        Parameters
        ----------
        value: (float) value of the absolute target positioning
        """

        value = self.check_bound(value)  #if user checked bounds, the defined bounds are applied here
        self.target_value = value
        value = self.set_position_with_scaling(value)  # apply scaling if the user specified one
        
        self.controller.move(value.value(), self.axis_value)  # when writing your own plugin replace this line
        self.emit_status(ThreadCommand('Update_Status', ['Actuator has move to the absolute target']))

    def move_rel(self, value: DataActuator):
        """ Move the actuator to the relative target actuator value defined by value

        Parameters
        ----------
        value: (float) value of the relative target positioning
        """
        value = self.check_bound(self.current_position + value) - self.current_position
        self.target_value = value + self.current_position
        value = self.set_position_relative_with_scaling(value)

        self.controller.move_rel(value.value(), self.axis_value) 
        self.emit_status(ThreadCommand('Update_Status', ['Actuator has move to the relative target']))

    def move_home(self):
        """Call the reference method of the controller"""

        self.controller.home(self.axis_value)  # when writing your own plugin replace this line
        self.emit_status(ThreadCommand('Update_Status', ['GSC has moved to home position']))

    def stop_motion(self):
      """Stop the actuator and emits move_done signal"""

      self.controller.stop()  # when writing your own plugin replace this line
      self.emit_status(ThreadCommand('Update_Status', ['GSC Actuator has stopped']))


if __name__ == '__main__':
    main(__file__)
