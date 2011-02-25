# Kontron IpmiLibrary
#
# author: Heiko Thiery <heiko.thiery@kontron.com>
# author: Michael Walle <michael.walle@kontron.com>
#

from errors import DecodingError, CompletionCodeError

LINK_INTERFACE_BASE           = 0x0
LINK_INTERFACE_FABRIC         = 0x1
LINK_INTERFACE_UPDATE_CHANNEL = 0x2

LINK_TYPE_BASE              = 0x01
LINK_TYPE_ETHERNET_FABRIC   = 0x02
LINK_TYPE_INFINIBAND_FABRIC = 0x03
LINK_TYPE_STARFABRIC_FABRIC = 0x04
LINK_TYPE_PCIEXPRESS_FABRIC = 0x05
LINK_TYPE_OEM0              = 0xf0
LINK_TYPE_OEM1              = 0xf1
LINK_TYPE_OEM2              = 0xf2
LINK_TYPE_OEM3              = 0xf3

LINK_TYPE_EXT_BASE0 = 0x00
LINK_TYPE_EXT_BASE1 = 0x01

LINK_TYPE_EXT_ETHERNET_FIX1000BX       = 0x00
LINK_TYPE_EXT_ETHERNET_FIX10GBX4       = 0x01
LINK_TYPE_EXT_ETHERNET_FCPI            = 0x02
LINK_TYPE_EXT_ETHERNET_FIX1000KX_10GKR = 0x03
LINK_TYPE_EXT_ETHERNET_FIX10GKX4       = 0x04
LINK_TYPE_EXT_ETHERNET_FIX40GKR4       = 0x05

LINK_TYPE_EXT_OEM_LINK_TYPE_EXT_0      = 0x00

LINK_FLAGS_LANE0    = 0x01
LINK_FLAGS_LANE0123 = 0x0f

LINK_STATE_DISABLE  = 0
LINK_STATE_ENABLE   = 1

CHANNEL_SIGNALING_CLASS_BASIC = 0
CHANNEL_SIGNALING_CLASS_10_3125GBD = 4

LED_STATE_LOCAL    = 0x01
LED_STATE_OVERRIDE = 0x02
LED_STATE_LAMPTEST = 0x04

LED_COLOR_BLUE     = 0x01
LED_COLOR_RED      = 0x02
LED_COLOR_GREEN    = 0x03
LED_COLOR_AMBER    = 0x04
LED_COLOR_ORANGE   = 0x05
LED_COLOR_WHITE    = 0x06

LED_FUNCTION_OFF       = 0x00
LED_FUNCTION_BLINKING  = 0x01
LED_FUNCTION_ON        = 0xff

FRU_CONTROL_OPTION_COLD_RESET = 0x00
FRU_CONTROL_OPTION_WARM_RESET = 0x01
FRU_CONTROL_OPTION_GRACEFUL_REBOOT = 0x02
FRU_CONTROL_OPTION_ISSUE_DIAGNOSTIC_INTERRUPT = 0x03
FRU_CONTROL_OPTION_QUIESCED = 0x04

NETFN_PICMG = 0x2c

CMD_FRU_CONTROL               = 0x04
CMD_GET_LED_STATE             = 0x08
CMD_SET_FRU_ACTIVATION_POLICY = 0x0a
CMD_GET_FRU_ACTIVATION_POLICY = 0x0b
CMD_SET_PORT_STATE            = 0x0e
CMD_SET_SIGNALING_CLASS       = 0x3b
CMD_GET_SIGNALING_CLASS       = 0x3c

PICMG_IDENTIFIER = 0x00


class Commands:
    def fru_control(self, fn, fru_id, option):
        req = [ NETFN_PICMG << 2 | 0, CMD_FRU_CONTROL, PICMG_IDENTIFIER,
                fru_id, option ]
        rsp = fn(req)
        if rsp[0] != 0x00:
            raise CompletionCodeError(rsp[0])

    def get_led_state(self, fn, fru_id, led_id):
        req = [ NETFN_PICMG << 2 | 0, CMD_GET_LED_STATE, PICMG_IDENTIFIER,
                fru_id, led_id ]
        rsp = fn(req)
        if rsp[0] != 0x00:
            raise CompletionCodeError(rsp[0])
        return LedState(rsp[1])

    def set_fru_activation_policy(self, fn, fru_id, mask_bits, set_bits):
        req = [ NETFN_PICMG << 2 | 0, CMD_SET_FRU_ACTIVATION_POLICY,
                 PICMG_IDENTIFIER, fru_id, mask_bits, set_bits ]
        rsp = fn(req)
        if rsp[0] != 0x00:
            raise CompletionCodeError(rsp[0])

    def set_port_state(self, fn, link_info):
        req = [ NETFN_PICMG << 2 | 0, CMD_SET_PORT_STATE,
                 PICMG_IDENTIFIER ] 
        req.extend(link_info.encode())
        rsp = fn(req)
        if rsp[0] != 0x00:
            raise CompletionCodeError(rsp[0])

    def set_signaling_class(self, fn, interface, channel, signaling_class):
        req = [ NETFN_PICMG << 2 | 0, CMD_SET_SIGNALING_CLASS, 
                PICMG_IDENTIFIER, (interface & 3)<<6|(channel & 0x3f), 
                signaling_class ]
        rsp = fn(req)
        if rsp[0] != 0x00:
            raise CompletionCodeError(rsp[0])

    def get_signaling_class(self, fn, interface, channel):
        req = [ NETFN_PICMG << 2 | 0, CMD_GET_SIGNALING_CLASS, 
                PICMG_IDENTIFIER, (interface & 3)<<6|(channel & 0x3f), 
                signaling_class ]
        rsp = fn(req)
        if rsp[0] != 0x00:
            raise CompletionCodeError(rsp[0])
        return rsp

class LinkInfo:
    def __init__(self, channel=None, interface=None, flags=None, 
            link_type=None, extension=None, group_id=None, state=None):
        self.channel = channel
        self.interface = interface
        self.flags = flags
        self.link_type = link_type
        self.extension = extension
        self.group_id = group_id
        self.state = state

    def encode(self):
        data = [0, 0, 0, 0, 0]
        data[0] = self.channel & 0x3f | (self.interface & 0x3) << 6
        data[1] = self.flags & 0xf | (self.link_type & 0xf) << 4
        data[2] = (self.link_type & 0xf0) >> 4 | (self.extension & 0xf) << 4
        data[3] = self.group_id
        data[4] = self.state
        return data

    def decode(self, data):
        raise RuntimeError('TBD')
 
class LedState:
    def __init__(self, data=None):
        if data:
            self.decode(data)

    def encode(self):
        raise RuntimeError('TBD')

    def decode(self, data):
        self.states = data[1]
        if data[2] in (LED_FUNCTION_ON, LED_FUNCTION_OFF):
            self.local_function = data[2]
        else:
            if data[2] in range(0xfb, 0xff):
                raise DecodingError()
            self.local_function = LED_FUNCTION_BLINKING
            self.local_off_duration = data[2]
            self.local_on_duration = data[3]

        self.local_function = data[2]
        self.local_color = data[4]

        if self.states & LED_STATE_OVERRIDE:
            self.override_function = data[5]
            self.override_on_duration = data[6]
            self.override_color = data[7]

        if self.states & LED_STATE_LAMPTEST:
            self.lamp_test_duration = data[8]

