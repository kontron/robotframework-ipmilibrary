#
# Kontron Ipmitool Interface
#
# author: Heiko Thiery <heiko.thiery@kontron.com>
#

from subprocess import Popen, PIPE

class IntfIpmitool:
    IPMITOOL = 'ipmitool'
    
    def open(self, **parameters):
        """Open the interface and set the ipmitool parameters
        """
        self._params = parameters

    def close(self):
        """Cloe the interface
        """
        
    def send_and_receive(raw_cmd, lun=0):
        """Send a IPMI command and return the received data
        `raw_cmd`
        `lun`
        """
        cmd = ('-l %d raw ' % lun)
        
        cmd_output = self._run_ipmitool(cmd)
        cmd_output = cmd_output.replace('\n','').replace('\r','')
        cmd_data = [int(x,16) for x in cmd_output.strip().split(' ')]
   
        return cmd_data
 
    def _run_ipmitool(self, ipmitool_cmd):
        """Lecacy call of ipmitool (will be removed in future)
        """
        cmd = self.IPMITOOL
        cmd += (' -I lan')
        cmd += (' -H %s' % self._params['host'])

        if 'bridge_channel' in self._params:
            cmd += (' -b %d' % self._params['bridge_channel'])

        if 'double_bridge_target_address' in self._params:
            cmd += (' -t 0x%02x' %
                    self._params['double_bridge_target_address'])
            cmd += (' -T 0x%02x' % self._params['target_address'])
        else:
            cmd += (' -t 0x%02x' % self._params['target_address'])

        cmd += (' -U "%s"' % self._params['user'])
        cmd += (' -P "%s"' % self._params['password'])
        cmd += (' %s' % ipmitool_cmd)
        cmd += (' 2>&1')

        child = Popen(cmd, shell=True, stdout=PIPE)
        output = child.communicate()[0]

        return output, child.returncode

