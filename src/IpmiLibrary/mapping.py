from utils import find_attribute
from sel import SelRecord
from picmg import Picmg, LedState
from bmc import Watchdog

def find_picmg_interface_type(type):
    return find_attribute(Picmg, type, 'PICMG_LINK_INTERFACE')

def find_picmg_link_type(type):
    return find_attribute(Picmg, type, 'PICMG_LINK_TYPE')

def find_picmg_link_type_extension(type):
    return find_attribute(Picmg, type, 'PICMG_LINK_TYPE_EXT')

def find_picmg_link_flags(flags):
    return find_attribute(Picmg, flags, 'PICMG_LINK_FLAGS')

def find_picmg_link_state(state):
    return find_attribute(Picmg, state, 'PICMG_LINK_STATE')

def find_picmg_signaling_class(signaling_class):
    return find_attribute(Picmg, signaling_class, 'PICMG_CHANNEL')

def find_picmg_led_state(state):
    return find_attribute(LedState, state, 'PICMG_LED_STATE')

def find_picmg_led_color(color):
    return find_attribute(LedState, color, 'PICMG_LED_COLOR')

def find_picmg_led_function(function):
    return find_attribute(LedState, function, 'PICMG_LED_FUNCTION')

def find_watchdog_action(action):
    return find_attribute(Watchdog, action, 'TIMEOUT_ACTION')

def find_event_direction(direction):
    return find_attribute(SelRecord, direction, 'EVENT_')

def find_sensor_type(type):
    return find_attribute(SelRecord, type, 'SENSOR_TYPE_')

