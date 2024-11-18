from typing import Union, List, Dict

from pymodaq.control_modules.move_utility_classes import DAQ_Move_base, comon_parameters_fun, main, DataActuatorType, \
    DataActuator  
from pymodaq.utils.daq_utils import ThreadCommand  
from pymodaq.utils.parameter import Parameter
from pymodaq_plugins_optosigma.hardware.gsc_VISADriver import GSC

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
    is_multiaxes = True 
    _axis_names: Union[List[str], Dict[str, int]] = {'X-Axis', "Y-Axis"}  
    _controller_units: Union[str, List[str]] = GSC.default_units  
    _epsilon: Union[float, List[float]] = 0.1 
    data_actuator_type = DataActuatorType.DataActuator  
    is_multiaxes = True 
    _axis_names: Union[List[str], Dict[str, int]] = {'Axis1':1, 'Axis2':2} 
    _controller_units: Union[
        str, List[str]] = GSC.default_units  
    _epsilon: Union[
        float, List[float]] = 1  
    data_actuator_type = DataActuatorType.DataActuator 

    params = [
                 {"title": "Instrument Address", "name": "visa_name", "type": "str", "value": "ASRL11::INSTR"},
                 {"title": "Speed_ini", "name": "speed_ini", "type": "int", "value": 10000},
                 {"title": "Speed_fin", "name": "speed_fin", "type": "int", "value": 10000},
                 {"title": "Acceleration time", "name": "acceleration_time", "type": "int", "value": 100},
             ] + comon_parameters_fun(is_multiaxes, axis_names=_axis_names, epsilon=_epsilon)

    def ini_attributes(self):
        self.controller: GSC = None

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

        raise NotImplementedError 
            if the parameter is not implemented
        """

        if param.name() == "speed_ini" or param.name() == "speed_fin" or param.name() == "acceleration_time":
            self.controller.set_speed(self.settings["speed_ini"], self.settings["speed_fin"],
                                      self.settings["acceleration_time"], self.axis_value)
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

        self.ini_stage_init(slave_controller=controller) 

        if self.is_master: 
            self.controller = GSC(self.settings["visa_name"])  
            self.controller.connect()

        info = "For once it actually worked....GSC Actuator initialized"
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
        self.emit_status(ThreadCommand('Update_Status', [f'Actuator has move to the absolute target'])) 

    def move_rel(self, value: DataActuator):
        """ Move the actuator to the relative target actuator value defined by value

        Parameters
        ----------
        value: (float) value of the relative target positioning
        """
        value = self.check_bound(self.current_position + value) - self.current_position
        self.target_value = value + self.current_position
        value = self.set_position_relative_with_scaling(value)

        self.controller.move_rel(int(value.value()), self.axis_value) 
        self.emit_status(ThreadCommand('Update_Status', ['Actuator has move to the relative target'])) 

    def move_home(self):
        """Call the reference method of the controller"""

        self.controller.home(self.axis_value) 
        self.emit_status(ThreadCommand('Update_Status', ['GSC has moved to home position']))

    def stop_motion(self):
        """Stop the actuator and emits move_done signal"""

        self.controller.stop(self.axis_value) 
        self.emit_status(ThreadCommand('Update_Status', ['GSC Actuator has stopped']))


if __name__ == '__main__':
    main(__file__)
