# Kontron IpmiLibrary
#
# author: Heiko Thiery <heiko.thiery@kontron.com>
#

from errors import DecodingError

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

class Commands:
    IPMI_NETFN_PICMG = 0x2c
    IPMI_CMDID_PICMG_GET_LED_STATE = 0x08
    IPMI_PICMG_IDENTIFIER = 0x00

    def get_led_state(self, fru_id, led_id):
        cmd = 'raw 0x2c 0x08 0 %d %d' % (fru_id, led_id)
        output = self._run_ipmitool_checked(cmd)
        output = output.replace('\n','').replace('\r','')
        data = [int(x,16) for x in output.strip().split(' ')]

        return LedState(data)

class LedState:
    PICMG_LED_STATE_LOCAL    = 0x01
    PICMG_LED_STATE_OVERRIDE = 0x02
    PICMG_LED_STATE_LAMPTEST = 0x04

    PICMG_LED_COLOR_BLUE     = 0x01
    PICMG_LED_COLOR_RED      = 0x02
    PICMG_LED_COLOR_GREEN    = 0x03
    PICMG_LED_COLOR_AMBER    = 0x04
    PICMG_LED_COLOR_ORANGE   = 0x05
    PICMG_LED_COLOR_WHITE    = 0x06

    PICMG_LED_FUNCTION_OFF       = 0x00
    PICMG_LED_FUNCTION_BLINKING  = 0x01
    PICMG_LED_FUNCTION_ON        = 0xff

    def __init__(self, data=None):
        if data:
            self.decode(data)

    def encode(self):
        raise RuntimeError('TBD')

    def decode(self, data):
        self.states = data[1]
        if data[2] in (self.PICMG_LED_FUNCTION_ON, self.PICMG_LED_FUNCTION_OFF):
            self.local_function = data[2]
        else:
            if data[2] in range(0xfb, 0xff):
                raise DecodingError()
            self.local_function = self.PICMG_LED_FUNCTION_BLINKING
            self.local_off_duration = data[2]
            self.local_on_duration = data[3]

        self.local_function = data[2]
        self.local_color = data[4]

        if self.states & self.PICMG_LED_STATE_OVERRIDE:
            self.override_function = data[5]
            self.override_on_duration = data[6]
            self.override_color = data[7]

        if self.states & self.PICMG_LED_STATE_LAMPTEST:
            self.lamp_test_duration = data[8]

