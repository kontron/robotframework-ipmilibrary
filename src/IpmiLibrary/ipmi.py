#
# Kontron IpmiLibrary
#
# author: Heiko Thiery <heiko.thiery@kontron.com>
#

from intf_ipmitool import IntfIpmitool


class IpmiConnection():
    def __init__(self, type='ipmitool'):
        if type == 'ipmitool':
            self._intf = IntfIpmitool()
        else:
            raise RuntimeError('unknown interface type %s' % type)

    def open(self, **parameters):
        """Open the interface connection
        
        the following interface configuration parameters can be assigned by
        dict:
        parameters['host'] 
        parameters['user']
        parameters['password']
        parameters['target_address']
        parameters['bridge_channel']
        parameters['double_bridge_target_address']
        """
        self._intf.open(**parameters)

    def close(self):
        """Close the interface connection
        """
        self._intf.close()


