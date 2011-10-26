import pyipmi
import pyipmi.picmg
import pyipmi.bmc
import pyipmi.sdr
import pyipmi.event
import pyipmi.constants
import pyipmi.hpm

from utils import find_attribute

# new
def find_fru_field_type_code(type_code):
    return find_attribute(pyipmi.fru.FruDataField, type_code, 'TYPE_')

def find_picmg_led_color(color):
    return find_attribute(pyipmi.picmg.LedState, color, 'COLOR_')

def find_picmg_led_function(function):
    return find_attribute(pyipmi.picmg.LedState, function, 'FUNCTION_')

def find_sdr_record_type(record_type):
    return find_attribute(pyipmi.sdr, record_type, 'SDR_TYPE_')

def find_entity_type_id(entity_id):
    return find_attribute(pyipmi.constants, entity_id, 'ENTITY_TYPE_')

# old ones.. should go away/be replaced soon
def find_picmg_interface_type(interface_type):
    return find_attribute(pyipmi.picmg.LinkInfo, interface_type,
            'INTERFACE')

def find_picmg_link_type(link_type):
    return find_attribute(pyipmi.picmg.LinkInfo, link_type, 'TYPE_')

def find_picmg_link_type_extension(extension):
    return find_attribute(pyipmi.picmg.LinkInfo, extension, 'TYPE_EXT_')

def find_picmg_link_flags(flags):
    return find_attribute(pyipmi.picmg.LinkInfo, flags, 'FLAGS_')

def find_picmg_link_state(state):
    return find_attribute(pyipmi.picmg.LinkInfo, state, 'STATE_')

def find_picmg_signaling_class(signaling_class):
    return find_attribute(pyipmi.picmg, signaling_class,
            'CHANNEL_SIGNALING_CLASS_')

def find_watchdog_action(action):
    return find_attribute(pyipmi.bmc.Watchdog, action,
            'TIMEOUT_ACTION_')

def find_watchdog_timer_use(timer_use):
    return find_attribute(pyipmi.bmc.Watchdog, timer_use,
            'TIMER_USE_')

def find_event_direction(direction):
    return find_attribute(pyipmi.event, direction, 'EVENT_')

def find_sensor_type(sensor_type):
    return find_attribute(pyipmi.sdr, sensor_type, 'SENSOR_TYPE_')

def find_lan_configuration_parameter(parameter):
    return find_attribute(pyipmi.lan, parameter, 'LAN_PARAMETER_')

def find_hpm_component_property(property):
    return find_attribute(pyipmi.hpm, property, 'PROPERTY_')
