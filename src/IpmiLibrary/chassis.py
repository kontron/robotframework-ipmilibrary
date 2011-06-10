#
# Kontron IpmiLibrary
#
# author: Michael Walle <michael.walle@kontron.com>
# author: Heiko Thiery <heiko.thiery@kontron.com>
#

class Chassis:
    def issue_chassis_power_down(self):
        """Sends a _chassis power down_ command.
        """
        self._ipmi.chassis_control_power_down()

    def issue_chassis_power_cycle(self):
        """Sends a _chassis power cycle_.
        """
        self._ipmi.chassis_control_power_cycle()

    def issue_chassis_power_reset(self):
        """Sends a _chassis power reset_.
        """
        self._ipmi.chassis_control_hard_reset()
