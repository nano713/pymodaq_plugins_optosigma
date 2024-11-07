import pyvisa 
import time
import logging
logger = logging.getLogger(__name__)

class AxisError(Exception):
    MESSAGES = {
        "K" : "Normal state", 
        "A" : "Other",
        "O" : "Overflow"    
    }
    def __init__(self, error_code):
        self.message = self.MESSAGES[error_code]
