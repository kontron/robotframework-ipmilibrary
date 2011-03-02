import pyipmi
import pyipmi.picmg

import sel
import bmc
from utils import find_attribute

# new
def find_picmg_led_color(color):
    return find_attribute(pyipmi.picmg.LedState, color, 'COLOR')

def find_picmg_led_function(function):
    return find_attribute(pyipmi.picmg.LedState, function, 'FUNCTION')

# old ones.. should go away/be replaced soon
def find_picmg_interface_type(interface_type):
    return find_attribute(pyipmi.picmg, interface_type, 'LINK_INTERFACE')

def find_picmg_link_type(link_type):
    return find_attribute(pyipmi.picmg, link_type, 'LINK_TYPE')

def find_picmg_link_type_extension(extension):
    return find_attribute(pyipmi.picmg, extension, 'LINK_TYPE_EXT')

def find_picmg_link_flags(flags):
    return find_attribute(pyipmi.picmg, flags, 'LINK_FLAGS')

def find_picmg_link_state(state):
    return find_attribute(pyipmi.picmg, state, 'LINK_STATE')

def find_picmg_signaling_class(signaling_class):
    return find_attribute(pyipmi.picmg, signaling_class,
            'CHANNEL_SIGNALING_CLASS')

def find_watchdog_action(action):
    return find_attribute(bmc, action, 'WATCHDOG_TIMEOUT_ACTION')

def find_watchdog_timer_use(timer_use):
    return find_attribute(bmc, timer_use, 'WATCHDOG_TIMER_USE')

def find_event_direction(direction):
    return find_attribute(sel, direction, 'EVENT_')

def find_sensor_type(sensor_type):
    return find_attribute(sel, sensor_type, 'SENSOR_TYPE_')

