import picmg
import bmc
import sel

from utils import find_attribute

def find_picmg_interface_type(type):
    return find_attribute(picmg, type, 'LINK_INTERFACE')

def find_picmg_link_type(type):
    return find_attribute(picmg, type, 'LINK_TYPE')

def find_picmg_link_type_extension(type):
    return find_attribute(picmg, type, 'LINK_TYPE_EXT')

def find_picmg_link_flags(flags):
    return find_attribute(picmg, flags, 'LINK_FLAGS')

def find_picmg_link_state(state):
    return find_attribute(picmg, state, 'LINK_STATE')

def find_picmg_signaling_class(signaling_class):
    return find_attribute(picmg, signaling_class, 'CHANNEL_SIGNALLING_CLASS')

def find_picmg_led_state(state):
    return find_attribute(picmg, state, 'LED_STATE')

def find_picmg_led_color(color):
    return find_attribute(picmg, color, 'LED_COLOR')

def find_picmg_led_function(function):
    return find_attribute(picmg, function, 'LED_FUNCTION')

def find_watchdog_action(action):
    return find_attribute(bmc, action, 'WATCHDOG_TIMEOUT_ACTION')

def find_watchdog_timer_use(timer_use):
    return find_attribute(bmc, timer_use, 'WATCHDOG_TIMER_USE')

def find_event_direction(direction):
    return find_attribute(sel, direction, 'EVENT_')

def find_sensor_type(type):
    return find_attribute(sel, type, 'SENSOR_TYPE_')

