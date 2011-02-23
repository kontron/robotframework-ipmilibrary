# Kontron IpmiLibrary
#
# author: Heiko Thiery <heiko.thiery@kontron.com>
#

from utils import find_attribute


class Picmg:
    PICMG_LINK_INTERFACE_BASE           = 0x0
    PICMG_LINK_INTERFACE_FABRIC         = 0x1
    PICMG_LINK_INTERFACE_UPDATE_CHANNEL = 0x2

    PICMG_LINK_TYPE_BASE              = 0x01
    PICMG_LINK_TYPE_ETHERNET_FABRIC   = 0x02
    PICMG_LINK_TYPE_INFINIBAND_FABRIC = 0x03
    PICMG_LINK_TYPE_STARFABRIC_FABRIC = 0x04
    PICMG_LINK_TYPE_PCIEXPRESS_FABRIC = 0x05
    PICMG_LINK_TYPE_OEM0              = 0xf0
    PICMG_LINK_TYPE_OEM1              = 0xf1
    PICMG_LINK_TYPE_OEM2              = 0xf2
    PICMG_LINK_TYPE_OEM3              = 0xf3

    PICMG_LINK_TYPE_EXT_BASE0 = 0x00
    PICMG_LINK_TYPE_EXT_BASE1 = 0x01

    PICMG_LINK_TYPE_EXT_ETHERNET_FIX1000BX       = 0x00
    PICMG_LINK_TYPE_EXT_ETHERNET_FIX10GBX4       = 0x01
    PICMG_LINK_TYPE_EXT_ETHERNET_FCPI            = 0x02
    PICMG_LINK_TYPE_EXT_ETHERNET_FIX1000KX_10GKR = 0x03
    PICMG_LINK_TYPE_EXT_ETHERNET_FIX10GKX4       = 0x04
    PICMG_LINK_TYPE_EXT_ETHERNET_FIX40GKR4       = 0x05

    PICMG_LINK_TYPE_EXT_OEM_LINK_TYPE_EXT_0      = 0x00
    
    PICMG_LINK_FLAGS_LANE0    = 0x01
    PICMG_LINK_FLAGS_LANE0123 = 0x0f

    PICMG_LINK_STATE_DISABLE  = 0
    PICMG_LINK_STATE_ENABLE   = 1

    PICMG_CHANNEL_SIGNALING_CLASS_BASIC = 0
    PICMG_CHANNEL_SIGNALING_CLASS_10_3125GBD = 4

    def _find_picmg_interface_type(self, type):
        return find_attribute(Picmg, type, 'PICMG_LINK_INTERFACE')

    def _find_picmg_link_type(self, type):
        return find_attribute(Picmg, type, 'PICMG_LINK_TYPE')

    def _find_picmg_link_type_extension(self, type):
        return find_attribute(Picmg, type, 'PICMG_LINK_TYPE_EXT')

    def _find_picmg_link_flags(self, flags):
        return find_attribute(Picmg, flags, 'PICMG_LINK_FLAGS')

    def _find_picmg_link_state(self, state):
        return find_attribute(Picmg, state, 'PICMG_LINK_STATE')

    def _find_picmg_signaling_class(self, signaling_class):
        return find_attribute(Picmg, signaling_class, 'PICMG_CHANNEL')

class PicmgLed:
    
    PICMG_LED_COLOR_BLUE   = 0x01
    PICMG_LED_COLOR_RED    = 0x02
    PICMG_LED_COLOR_GREEN  = 0x03
    PICMG_LED_COLOR_AMBER  = 0x04
    PICMG_LED_COLOR_ORANGE = 0x05
    PICMG_LED_COLOR_WHITE  = 0x06

    PICMG_LED_FUNCTION_OFF = 0x00
    PICMG_LED_FUNCTION_ON  = 0xff

    def __init__(self, state_data):
        self._states = state_data[1]
        self._local_function = state_data[2] 
        self._local_on_duration = state_data[3]
        self._local_color = state_data[4]
        if (self._states & 0x2):
            self._override_function = state_data[5] 
            self._override_on_duration = state_data[6] 
            self._override_color = state_data[7]
        if (self._states & 0x4):
            self._lamp_test_duration = state_data[8]

    def _find_picmg_led_color(self, color):
        return find_attribute(PicmgLed, color, 'PICMG_LED_COLOR')

    def _find_picmg_led_function(self, function):
        return find_attribute(PicmgLed, function, 'PICMG_LED_FUNCTION')
