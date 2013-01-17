#
# Kontron IpmiLibrary
#
# author: Michael Walle <michael.walle@kontron.com>
# author: Heiko Thiery <heiko.thiery@kontron.com>
#
from robot import utils
from robot.utils import asserts
from robot.utils.connectioncache import ConnectionCache
from robot.output import LOGGER
from robot.output.loggerhelper import Message

from utils import int_any_base
from mapping import *

class Picmg:
    def get_picmg_properties(self):
        return self._ipmi.get_picmg_properties()

    def activate_fru(self, fruid=0):
        """Sends a _Set FRU Activation_ command to the given fru."""
        fruid = int(fruid)
        self._ipmi.set_fru_activation(fruid)

    def deactivate_fru(self, fruid=0):
        """Sends a _Set FRU Deactivation_ command to the given fru."""
        fruid = int(fruid)
        self._ipmi.set_fru_deactivation(fruid)

    def clear_activation_lock_bit(self, fruid=0):
        """Clears the activation lock bit for to the given FRU.
        """
        fruid = int(fruid)
        self._ipmi.clear_fru_activation_lock(fruid)

    def clear_deactivation_lock_bit(self, fruid=0):
        """Clears the deactivation lock bit for to the given FRU.
        """
        fruid = int(fruid)
        self._ipmi.clear_fru_deactivation_lock(fruid)

    def issue_frucontrol_cold_reset(self, fruid=0):
        """Sends a _frucontrol cold reset_ to the given FRU.
        """
        fruid = int(fruid)
        self._ipmi.fru_control_cold_reset(fruid)

    def issue_frucontrol_diagnostic_interrupt(self, fruid=0):
        """Sends a _frucontrol diagnostic interrupt_ to the given FRU.
        """
        fruid = int(fruid)
        self._ipmi.fru_control_diagnostic_interrupt(fruid)

    def get_fru_led_state(self, fru_id, led_id):
        """Returns the FRU LED state.
        """
        fru_id = int(fru_id)
        led_id = int(led_id)

        self._cp['led_state'] = self._ipmi.get_led_state(fru_id, led_id)

        self._debug('LED state is %s' % self._cp['led_state'])

    def led_color_should_be(self, expected_color, msg=None, values=True):
        """Fails if Picmg FRU Led color is not as given value.

        `expected_color` value can be:
        Blue, Red, Green, Amber, Orange, White
        """
        expected_color = find_picmg_led_color(expected_color)
        if self._cp['led_state'].override_enabled:
            actual_color = self._cp['led_state'].override_color
        else:
            actual_color = self._cp['led_state'].local_color

        asserts.fail_unless_equal(expected_color, actual_color, msg, values)

    def led_function_should_be(self, expected_function, msg=None, values=True):
        """Fails if Picmg FRU Led function is not as given value.

        `expected_function` value can be:
        ON, OFF
        """
        expected_function = find_picmg_led_function(expected_function)
        if self._cp['led_state'].override_enabled:
            actual_function = self._cp['led_state'].override_function
        else:
            actual_function = self._cp['led_state'].local_function

        asserts.fail_unless_equal(expected_function, actual_function, msg,
                values)

    def led_state_should_be(self, expected_state, msg=None, values=True):
        """Fails if Picmg FRU Led State is not as given value.

        `expecte_state` value can be:
        Local Control, Override, Lamp Test
        """
        ac = self._active_connection
        expected_state = find_picmg_led_function(expected_state)
        if ac._led.override_enabled:
            pass
        elif ac._led.override_enabled:
            function = ac._led.override_function
        else:
            function = ac._led.local_function
        asserts.fail_unless_equal(expected_function, function, msg, values)

    def set_port_state(self, interface, channel, flags, link_type,
            link_type_ext, state, link_class=0):
        """Sends the "PICMG Set Portstate" command.

        `interface` is one of the following interface types: BASE, FABRIC,
        UPDATE_CHANNEL.

        `channel` is the interface channel ID. `flags` is the lane mask and one
        of the following values: LANE0, LANE0123.

        `link_type` is one of the following values: BASE, ETHERNET_FABRIC,
        INFINIBAND_FABRIC, STARFABRIC_FABRIC, PCIEXPRESS_FABRIC.

        `link_class` is the channel signaling class capability and hast to be
        one of the following values: CLASS_BASIC, CLASS_10_3125GBD.

        `link_type_ext` is one of the following values: BASE0, BASE1,
        ETHERNET_FIX1000_BX, ETHERNET_FIX10GB_X4, ETHERNET_FCPI,
        ETHERNET_FIX1000KX_10G_KR, ETHERNET_FIX10GK_X4, ETHERNET_FIX40G_KR4

        `state` is the link state and has to be one of the following values:
        ENABLE, DISABLE.

        Note: Link Grouping ID is not supported yet

        Example:
        | Set Port State | BASE | 1 | LANE0 | BASE | BASE0 | ENABLE
        """

        link_descr = pyipmi.picmg.LinkDescriptor()
        link_descr.interface = find_picmg_interface_type(interface)
        link_descr.channel = int(channel)
        link_descr.link_flags = find_picmg_link_flags(flags)
        link_descr.type = find_picmg_link_type(link_type)
        link_descr.sig_class = find_picmg_link_signaling_class(link_class)
        link_descr.extension = find_picmg_link_type_extension(link_type_ext)
        link_descr.grouping_id = 0
        state = find_picmg_link_state(state)
        self._ipmi.set_port_state(link_descr, state)

    def get_power_level(self, fruid, power_type, offset):
        """return the specified power level for the fru
        `fruid`

        `power_type`

        `offset`

        """
        fruid = int_any_base(fruid)
        power_type = int_any_base(power_type)
        offset = int_any_base(offset)

        pwr = self._ipmi.get_power_level(fruid, power_type)
        return pwr.power_levels[offset]

    def get_fan_speed_properties(self, fruid):
        """
        """
        fruid = int_any_base(fruid)
        return self._ipmi.get_fan_speed_properties(fruid)

    def get_fan_override_level(self, fruid):
        """
        """
        fruid = int_any_base(fruid)
        (override_level, local_level) = self._ipmi.get_fan_level(fruid)
        return override_level

    def set_signaling_class(self, interface, channel, signaling_class):
        """*DEPRECATED* Sends the `Set Channel Siganling Class` command.

        `interface` the interface type (BASE, FABRIC, UPDATE_CHANNEL)

        `channel` is the interface channel ID.

        `class` is the channel signaling class capability and hast to be one of
        the following values: CLASS_BASIC, CLASS_10_3125GBD.
        """

        interface = find_picmg_interface_type(interface)
        channel = int(channel)
        signaling_class = find_picmg_signaling_class(signaling_class)
        self._ipmi.set_signaling_class(interface, channel, signaling_class)

    def get_signaling_class(self, interface, channel):
        """*DEPRECATED* Sends `Get Channel Signaling Class` command
        """

        interface = find_picmg_interface_type(interface)
        channel = int(channel)
        self._ipmi.get_signaling_class(interfac, channel)
