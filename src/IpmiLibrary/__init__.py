#
# Kontron IpmiLibrary
#
# author: Michael Walle <michael.walle@kontron.com>
# author: Heiko Thiery <heiko.thiery@kontron.com>
#

import logging
import time
from sel import SelRecord
from subprocess import Popen, PIPE

from robot import utils
from robot.utils import asserts
from robot.utils.connectioncache import ConnectionCache
from robot.output import LOGGER
from robot.output.loggerhelper import Message
import robot.version

import pyipmi
import pyipmi.logger
import pyipmi.interfaces

from utils import int_any_base
from mapping import *

from sdr import Sdr
from sel import Sel
from fru import Fru
from bmc import Bmc
from picmg import Picmg
from hpm import Hpm
from chassis import Chassis

class RobotLogHandler(logging.Handler):
    # mappping from logging to robots log levels
    mapping = {
            'NOTSET'   : 'NONE',
            'DEBUG'    : 'DEBUG',
            'INFO'     : 'INFO',
            'WARNING'  : 'WARN',
            'ERROR'    : 'ERROR',
            'CRITICAL' : 'ERROR',
    }
    def __init__(self):
        logging.Handler.__init__(self)
        # format it the way robotframework understands it
        self.setFormatter(logging.Formatter("*%(levelname)s* %(message)s"))
    def emit(self, record):
        msg = record.getMessage()
        lvl = self.mapping[record.levelname]
        LOGGER.log_message(Message(msg, lvl))


if tuple(robot.version.VERSION.split('.')) <= (2,5):
    # add log handler to pyipmi
    pyipmi.logger.add_log_handler(RobotLogHandler())
    pyipmi.logger.set_log_level(logging.DEBUG)


class TimeoutError(Exception):
    pass


class IpmiConnection():
    def __init__(self, ipmi):
        self._ipmi = ipmi
        self._properties = {}
        self._sel_records = []
        self._selected_sel_record = None
        self._sdr_list = []
        self._selected_sdr = None

    def close(self):
        self._ipmi.session.close()


class IpmiLibrary(Sdr, Sel, Fru, Bmc, Picmg, Hpm, Chassis):
    def __init__(self, timeout=3.0, poll_interval=1.0):
        self._cache = ConnectionCache()
        self._timeout = timeout
        self._poll_interval = poll_interval

    @property
    def _ipmi(self):
        """Currently active connection."""
        return self._active_connection._ipmi

    @property
    def _cp(self):
        """Property storage per connection."""
        return self._active_connection._properties

    def wait_until_rmcp_is_ready(self, host, timeout=45):
        """Waits until the host can handle RMCP packets.

        `timeout` is given in Robot Framework's time format
        (e.g. 1 minute 20 seconds) that is explained in the User Guide.
        """

        timeout = utils.timestr_to_secs(timeout)

        start_time = time.time()
        while time.time() < start_time + timeout:
            try:
                self._ipmi.session.rmcp_ping()
                return
            except TimeoutError:
                pass

        raise AssertionError('RMCP not ready in %s.'
                % (utils.secs_to_timestr(timeout)))

    def open_ipmi_connection(self, host, target_address, user='', password='',
            routing_information=[(0x20,0)], interface='ipmitool', alias=None):
        """Opens a LAN connection to an IPMI shelf manager.

        `host` is the IP or hostname of the shelf manager. `target_address` the
        IPMI address to which the command should be sent. `user` and `password`
        are used to authenticate against the shelf manager.
        """

        host = str(host)
        target_address = int_any_base(target_address)
        user = str(user)
        password = str(password)

        if alias:
            alias = str(alias)

        interface = pyipmi.interfaces.create_interface(interface)
        ipmi = pyipmi.create_connection(interface)
        ipmi.session.set_session_type_rmcp(host)
        ipmi.session.set_auth_type_user(user, password)
        ipmi.target = pyipmi.Target(target_address)
        ipmi.target.set_routing_information(routing_information)

        self._info('Opening IPMI connection to %s:%s' % (host,
            target_address))

        ipmi.session.establish()

        connection = IpmiConnection(ipmi)

        self._active_connection = connection

        return self._cache.register(connection, alias)

    def switch_ipmi_connection(self, index_or_alias):
        """Switches between active connections using an index or alias.

        The index is got from `Open IPMI Connection` keyword, and an alias can
        be given to it.

        Returns the index of previously active conection.
        """

        old_index = self._cache.current_index
        self._active_connection = self._cache.switch(index_or_alias)
        return old_index

    def close_all_ipmi_connections(self):
        """Closes all open connections and empties the connection cache.

        After this keyword, new indexes got from the `Open Connection`
        keyword are reset to 1.

        This keyword should be used in a test or suite teardown to
        make sure all connections are closed.
        """
        self._active_connection = self._cache.close_all()

    def close_ipmi_connection(self, loglevel=None):
        """Closes the current connection.
        """
        self._ipmi.session.close()

    def wait_until_connection_is_ready(self):
        """*DEPRECATED*"""
        start_time = time.time()
        while time.time() < start_time + self._timeout:
            output, rc = self._ipmi.interface._run_ipmitool(
                    self._ipmi.target, 'bmc info')
            if rc != 0:
                time.sleep(self._poll_interval)
            else:
                return

    def _run_ipmitool_checked(self, cmd):
        """*DEPRECATED*"""
        output, rc = self._ipmi.interface._run_ipmitool(
                self._ipmi.target, cmd)
        if rc != 0:
            raise AssertionError('return code was %d' % rc)
        return output

    def set_timeout(self, timeout):
        """Sets the timeout used in `Wait Until X` keywords to the given value.

        `timeout` is given in Robot Framework's time format
        (e.g. 1 minute 20 seconds) that is explained in the User Guide.

        The old timeout is returned and can be used to restore it later.

        Example.
        | ${tout}= | Set Timeout | 2 minute 30 seconds |
        | Do Something |
        | Set Timeout | ${tout} |
        """

        old = getattr(self, '_timeout', 3.0)
        self._timeout = utils.timestr_to_secs(timeout)
        return utils.secs_to_timestr(old)

    def set_poll_interval(self, poll_interval):
        """Sets the poll interval used in `Wait Until X` keywords to the given
        value.

        `poll_interval` is given in Robot Framework's time format.

        The old poll interval is returend.

        For more details see `Set Timeout`.
        """

        old = getattr(self, '_poll_interval', 1.0)
        self._poll_interval = utils.timestr_to_secs(poll_interval)
        return utils.secs_to_timestr(old)

    def send_raw_command(self, *bytes):
        """Sends a raw IPMI command.

        `bytes` can either be a list or serveral scalar values.
        If a LUN other then zero is needed, it can be given with the first
        value of the list by prepending 'lun=', eg. lun=3.

        Example:
        | ${values}= | Create List | 0x06 | 0x01 | |
        | Send Raw Command | ${values} |  |  | | # BMC info command
        | Send Raw Command | 0x06 | 0x01 | | | # same as above
        | Send Raw Command | lun=3 | 0x3e | 0x62 | ... | # LUN other than zero
        """

        if isinstance(bytes[0], list):
            bytes = bytes[0]

        lun = 0
        if len(bytes) > 0 and bytes[0].startswith('lun='):
            lun = int_any_base(bytes[0][4:])
            bytes = bytes[1:]

        if len(bytes) < 2:
            raise RuntimeError('netfn and/or cmdid missing')

        bytes = [ int_any_base(b) for b in bytes ]
        bytes[0] = bytes[0] << 2 | lun
        req = ''.join([chr(b) for b in bytes])
        rsp = self._ipmi.raw_command(req)

        return [ord(b) for b in rsp]

    def _warn(self, msg):
        self._log(msg, 'WARN')

    def _info(self, msg):
        self._log(msg, 'INFO')

    def _debug(self, msg):
        self._log(msg, 'DEBUG')

    def _trace(self, msg):
        self._log(msg, 'TRACE')

    def _log(self, msg, level=None):
        self._is_valid_log_level(level, raise_if_invalid=True)
        msg = msg.strip()
        if level is None:
            level = self._default_log_level
        if msg != '':
            print '*%s* %s' % (level.upper(), msg)

    def _is_valid_log_level(self, level, raise_if_invalid=False):
        if level is None:
            return True
        if isinstance(level, basestring) and \
                level.upper() in ['TRACE', 'DEBUG', 'INFO', 'WARN', 'HTML']:
            return True
        if not raise_if_invalid:
            return False
        raise AssertionError("Invalid log level '%s'" % level)

