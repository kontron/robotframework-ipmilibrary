# Copyright 2014 Kontron Europe GmbH
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import pyipmi
import pyipmi.picmg
import pyipmi.bmc
import pyipmi.sdr
import pyipmi.sensor
import pyipmi.event
import pyipmi.constants
import pyipmi.hpm
import pyipmi.lan

from .utils import find_attribute

# new
def find_fru_field_type_code(type_code):
    return find_attribute(pyipmi.fru.FruDataField, type_code, 'TYPE_')

def find_picmg_led_color(color):
    return find_attribute(pyipmi.picmg.LedState, color, 'COLOR_')

def find_picmg_led_function(function):
    return find_attribute(pyipmi.picmg.LedState, function, 'FUNCTION_')

def find_sdr_record_type(record_type):
    return find_attribute(pyipmi.sdr, record_type, 'SDR_TYPE_')

def find_sdr_sensor_type(sensor_type):
    return find_attribute(pyipmi.sensor, sensor_type, 'SENSOR_TYPE_')

def find_entity_type_id(entity_id):
    return find_attribute(pyipmi.constants, entity_id, 'ENTITY_ID_')

def find_picmg_multirecord_id(record_id):
    return find_attribute(pyipmi.fru.FruPicmgRecord, record_id, 'PICMG_RECORD_ID_')

# old ones.. should go away/be replaced soon
def find_picmg_interface_type(interface_type):
    return find_attribute(pyipmi.picmg.LinkDescriptor, interface_type,
            'INTERFACE')

def find_picmg_link_type(link_type):
    return find_attribute(pyipmi.picmg.LinkDescriptor, link_type, 'TYPE_')

def find_picmg_link_type_extension(extension):
    return find_attribute(pyipmi.picmg.LinkDescriptor, extension, 'TYPE_EXT_')

def find_picmg_link_flags(flags):
    return find_attribute(pyipmi.picmg.LinkDescriptor, flags, 'FLAGS_')

def find_picmg_link_state(state):
    return find_attribute(pyipmi.picmg.LinkDescriptor, state, 'STATE_')

def find_picmg_link_signaling_class(signaling_class):
    return find_attribute(pyipmi.picmg.LinkDescriptor, signaling_class,
            'SIGNALING_')

def find_watchdog_action(action):
    return find_attribute(pyipmi.bmc.Watchdog, action,
            'TIMEOUT_ACTION_')

def find_watchdog_timer_use(timer_use):
    return find_attribute(pyipmi.bmc.Watchdog, timer_use,
            'TIMER_USE_')

def find_event_direction(direction):
    return find_attribute(pyipmi.event, direction, 'EVENT_')

def find_sensor_type(sensor_type):
    return find_attribute(pyipmi.sensor, sensor_type, 'SENSOR_TYPE_')

def find_lan_configuration_parameter(parameter):
    return find_attribute(pyipmi.lan, parameter, 'LAN_PARAMETER_')

def find_lan_ip_source(source):
    return find_attribute(pyipmi.lan, source,
            'LAN_PARAMETER_IP_ADDRESS_SOURCE_')

def find_hpm_component_property(property):
    return find_attribute(pyipmi.hpm, property, 'PROPERTY_')

def find_hpm_upgrade_action(action):
    return find_attribute(pyipmi.hpm, action, 'ACTION_')


import unittest

class TestFind(unittest.TestCase):
    def test_find_sdr_record_type(self):
        val = find_sdr_record_type('FULL Sensor Record')
        self.assertEqual(val, 0x1)

    def test_find_entity_type_id(self):
        val = find_entity_type_id('PICMG Front Board')
        self.assertEqual(val, 0xa0)
