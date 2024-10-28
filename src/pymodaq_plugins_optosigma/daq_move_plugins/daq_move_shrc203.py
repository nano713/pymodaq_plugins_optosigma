from typing import Union, List, Dict

from pymodaq.control_modules.move_utility_classes import DAQ_Move_base, comon_parameters_fun, main, DataActuatorType,\
    DataActuator  # common set of parameters for all actuators
from pymodaq.utils.daq_utils import ThreadCommand # object used to send info back to the main thread
from pymodaq.utils.parameter import Parameter
from pymodaq_plugins_optosigma.hardware.shrc203_VISADriver import SHRC203VISADriver as SHRC203
from pymodaq.utils.logger import set_logger, get_module_name
logger = set_logger(get_module_name(__file__))

# DK - follow the naming convention. this file name should be daq_move_SHRC203. See
# https://pymodaq.cnrs.fr/en/4.4.x/developer_folder/instrument_plugins.html#naming-convention.

class DAQ_Move_SHRC203(DAQ_Move_base):
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
    # DK - use the multiaxis feature with dictionary format {"X":1, ...}
    is_multiaxes = True  # TODO for your plugin set to True if this plugin is controlled for a multiaxis controller
    _axis_names: Union[List[str], Dict[str, int]] = {"X":1, "Y":2, "Z":3} 
    # DK - It may be good to use 'm' unit to apply _controller_units feature. I am afraid that mm becomes kilo micrometers k um
    _controller_units: Union[str, List[str]] = 'um'  # TODO for your plugin: put the correct unit here, it could be
    # TODO  a single str (the same one is applied to all axes) or a list of str (as much as the number of axes)
    # DK - Consider that the minimum increment of the stage is 50 nm. Then the epsilon should be ... ?
    _epsilon: Union[
        float, List[float]] = 0.1  # TODO replace this by a value that is correct depending on your controller
    # TODO it could be a single float of a list of float (as much as the number of axes)
    # Leave this as it is.
    data_actuator_type = DataActuatorType.DataActuator  # wether you use the new data style for actuator otherwise set this
    # as  DataActuatorType.float  (or entirely remove the line)
params = [
    
    # DK - create 'rsrc_name', 'speed_ini', 'speed...', 'loop' parameters where the speed parameter has children (= list)
    params = [ {'title': 'Serial Number:', 'name': 'serial_number', 'type': 'list', 'limits': rsrc_name, 'value': rsrc_name[0]},
              {'title1': 'Loop:', 'name': 'loop', 'type': 'int', 'value': 0},
              {'title2': 'Speed:', 'name': 'speed_ini', 'type': 'float', 'value': 0}, 
                {'title3': 'Acceleration:', 'name': 'accel_t', 'type': 'float', 'value': 1},
                {'title4': 'Speed:', 'name': 'speed_fin', 'type': 'float', 'value': 1.2}, 
              
             ] + comon_parameters_fun(is_multiaxes, axis_names=_axis_names, epsilon=_epsilon)

    # _epsilon is the initial default value for the epsilon parameter allowing pymodaq to know if the controller reached
    # the target value. It is the developer responsibility to put here a meaningful value

    def ini_attributes(self):
        self.stage: SHRC203 = None
        self.axis_value = 1  

    # DK data = self.controller.get_position(self.axis_value) See example in https://github.com/nano713/pymodaq_plugins_thorlabs/blob/dev/kpz_plugin/src/pymodaq_plugins_thorlabs/daq_move_plugins/daq_move_BrushlessDCMotor.py
    def get_actuator_value(self):
        """Get the current value from the hardware with scaling conversion.

        Returns
        -------
        float: The position obtained after scaling conversion.
        """
        pos = DataActuator(
            data=self.stage.get_position(self.axis_value))  # when writing your own plugin replace this line
        pos = self.get_position_with_scaling(pos)
        return pos

    # DK - delete as instructed
    # def user_condition_to_reach_target(self) -> bool:
    #     """ Implement a condition for exiting the polling mechanism and specifying that the
    #     target value has been reached

    #    Returns
    #     -------
    #     bool: if True, PyMoDAQ considers the target value has been reached
    #     """
    #     # TODO either delete this method if the usual polling is fine with you, but if need you can
    #     #  add here some other condition to be fullfilled either a completely new one or
    #     #  using or/and operations between the epsilon_bool and some other custom booleans
    #     #  for a usage example see DAQ_Move_brushlessMotor from the Thorlabs plugin
    #     return True

    # run close method
    def close(self):
        """Terminate the communication protocol"""
        ## TODO for your custom plugin
        return self.stage.close()
        #  self.controller.your_method_to_terminate_the_communication()  # when writing your own plugin replace this line

    # DK - implement speed, loop, ...
    def commit_settings(self, param: Parameter):
        """Apply the consequences of a change of value in the detector settings

        Parameters
        ----------
        param: Parameter
            A given parameter (within detector_settings) whose value has been changed by the user
        """
        default_units = 'um' # default units for the stage
        if param.name() == 'speed_ini' or param.name() == 'speed_fin' or param.name() == 'accel_t':
            self.speed_ini = self.stage.set_speed(self.speed_ini, self.speed_fin, self.accel_t, self.axis_value)
            #TODO How do we do this is the speed is being called from a dictionary before hand.....

            # do this only if you can and if the units are not known beforehand, for instance
            # if the motors connected to the controller are of different type (mm, µm, nm, , etc...)
            # see BrushlessDCMotor from the thorlabs plugin for an exemple

        elif param.name() == "loop":
            self.stage.set_loop()
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
        self.ini_stage_init(slave_controller=controller)  # will be useful when controller is slave

        if self.is_master:  # is needed when controller is master
            self.stage = SHRC203()  # arguments for instantiation!)
            # todo: enter here whatever is needed for your controller initialization and eventual
            #  opening of the communication channel

        info = "I'm not sure this works" # DK - replace this line with the actual info
        initialized = self.stage.open_connection()  # initialized = True
        return info, initialized

    # DK - use move method
    def move_abs(self, value: DataActuator):
        """ Move the actuator to the absolute target defined by value

        Parameters
        ----------
        value: (float) value of the absolute target positioning
        """

        value = self.check_bound(value)  # if user checked bounds, the defined bounds are applied here
        self.target_value = value
        value = self.set_position_with_scaling(value)  # apply scaling if the user specified one
       
        self.stage.move(
            value.value())  # when writing your own plugin replace this line
        self.emit_status(ThreadCommand('Update_Status', ['Some info you want to log']))

    # DK - use move_relative method
    def move_rel(self, value: DataActuator):
        """ Move the actuator to the relative target actuator value defined by value

        Parameters
        ----------
        value: (float) value of the relative target positioning
        """
        value = self.check_bound(self.current_position + value) - self.current_position
        self.target_value = value + self.current_position
        value = self.set_position_relative_with_scaling(value)

        self.stage.move_relative(
            value.value())  # when writing your own plugin replace this line
        self.emit_status(ThreadCommand('Update_Status', ['Some info you want to log']))

    # DK - use home method
    def move_home(self):
        """Call the reference method of the controller"""
        self.stage.home()  # when writing your own plugin replace this line
        self.emit_status(ThreadCommand('Update_Status', ['Some info you want to log']))

    # DK - use stop method
    def stop_motion(self):
        """Stop the actuator and emits move_done signal"""
        self.stage.stop()  # when writing your own plugin replace this line
        self.emit_status(ThreadCommand('Update_Status', ['Instrument stopped']))

    if __name__ == '__main__':
        main(__file__)