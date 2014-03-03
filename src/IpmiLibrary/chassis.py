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

class Chassis:
    def issue_chassis_power_up(self):
        """Sends a _chassis power up_ command.
        """
        self._ipmi.chassis_control_power_up()

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
