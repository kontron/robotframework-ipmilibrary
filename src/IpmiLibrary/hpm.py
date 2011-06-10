#
# Kontron IpmiLibrary
#
# author: Michael Walle <michael.walle@kontron.com>
# author: Heiko Thiery <heiko.thiery@kontron.com>
#

class Hpm:
    def hpm_start_firmware_upload(self, file_path, filename):
        """
        """
        cmd = 'hpm upgrade %s/%s all' % (file_path, filename)
        self._run_ipmitool_checked(cmd)

    def hpm_start_firmware_activation(self):
        """
        """
        cmd = 'hpm activate'
        self._run_ipmitool_checked(cmd)

    def hpm_start_firmware_rollback(self):
        """
        """
        cmd = 'hpm rollback'
        self._run_ipmitool_checked(cmd)


