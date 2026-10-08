import array
import os
import unittest
from unittest import mock

import pyipmi
from pyipmi.errors import IpmiTimeoutError

from IpmiLibrary import IpmiLibrary, IpmiConnection
from IpmiLibrary import mapping

SRC_DIR = os.path.join(os.path.dirname(__file__), '..', 'src', 'IpmiLibrary')


class TestNames(unittest.TestCase):
    def test_no_undefined_names(self):
        """Every name used by the library must exist.

        The modules use `from .mapping import *`, pyflakes can only report
        the names it cannot resolve as "may be undefined". Check them
        against the names mapping really provides.
        """
        from pyflakes import api, messages, reporter

        class Collector(reporter.Reporter):
            def __init__(self):
                self.messages = []

            def flake(self, message):
                self.messages.append(message)

            def syntaxError(self, *args):
                raise AssertionError('syntax error: %s' % (args,))

            def unexpectedError(self, *args):
                raise AssertionError('unexpected error: %s' % (args,))

        collector = Collector()
        api.checkRecursive([SRC_DIR], collector)

        undefined = []
        for m in collector.messages:
            if isinstance(m, messages.UndefinedName):
                undefined.append(str(m))
            elif isinstance(m, messages.ImportStarUsage):
                name = m.message_args[0]
                if not hasattr(mapping, name):
                    undefined.append(str(m))
        self.assertEqual(undefined, [])


class LibraryTestCase(unittest.TestCase):
    def setUp(self):
        self.lib = IpmiLibrary(poll_interval=0)
        self.ipmi = mock.Mock(spec=pyipmi.Ipmi)
        self.ipmi.session = mock.Mock()
        self.ipmi.interface = mock.Mock()
        self.lib._active_connection = IpmiConnection(self.ipmi, None)


class TestConnection(LibraryTestCase):
    def test_close_twice_closes_once(self):
        self.lib.close_ipmi_connection()
        self.lib.close_ipmi_connection()
        self.assertEqual(self.ipmi.close.call_count, 1)

    def test_failed_open_closes_interface(self):
        ipmi = mock.Mock()
        ipmi.open.side_effect = RuntimeError('auth')
        with self.assertRaises(RuntimeError):
            IpmiLibrary._open_ipmi(ipmi)
        ipmi.close.assert_called_once()

    @mock.patch('pyipmi.Ipmi')
    @mock.patch('pyipmi.interfaces.create_interface')
    def test_lan_connection_default_interface(self, create_interface, _):
        self.lib.open_ipmi_lan_connection('host', '0x20')
        create_interface.assert_called_once_with('rmcp')

    @mock.patch('pyipmi.Ipmi')
    @mock.patch('pyipmi.interfaces.create_interface')
    def test_lan_connection_retries(self, create_interface, _):
        self.lib.open_ipmi_lan_connection('host', '0x20',
                interface_type='ipmitool', max_retries='2')
        create_interface.assert_called_with('ipmitool', retries=2)
        self.lib.open_ipmi_lan_connection('host', '0x20',
                interface_type='rmcpplus', max_retries='2')
        create_interface.assert_called_with('rmcpplus', max_retries=2)

    @mock.patch('pyipmi.Ipmi')
    @mock.patch('pyipmi.interfaces.create_interface')
    def test_rmcp_connection_returns_index(self, create_interface, _):
        self.assertEqual(self.lib.open_ipmi_rmcp_connection('host', '0x20'),
                1)

    def test_wait_until_rmcp_is_ready_retries(self):
        self.ipmi.session.rmcp_ping.side_effect = [IpmiTimeoutError(),
                IpmiTimeoutError(), None]
        self.lib.wait_until_rmcp_is_ready(5)
        self.assertEqual(self.ipmi.session.rmcp_ping.call_count, 3)

    def test_wait_until_rmcp_is_ready_without_ping(self):
        self.ipmi.interface = mock.Mock(spec=[])
        self.ipmi.interface.NAME = 'rmcp'
        self.lib.wait_until_rmcp_is_ready(5)
        self.ipmi.session.rmcp_ping.assert_not_called()


class TestRaw(LibraryTestCase):
    def test_send_raw_command(self):
        self.ipmi.send_raw.return_value = b'\x00\x20'
        self.assertEqual(self.lib.send_raw_command('0x06', '0x01'), [0, 0x20])
        self.ipmi.send_raw.assert_called_once_with(0, netfn=6,
                raw_bytes=b'\x01')

    def test_send_raw_command_with_integers(self):
        self.ipmi.send_raw.return_value = b'\x00'
        self.lib.send_raw_command(6, 1)
        self.ipmi.send_raw.assert_called_once_with(0, netfn=6,
                raw_bytes=b'\x01')


class TestLan(LibraryTestCase):
    def test_get_ip_address(self):
        self.ipmi.get_lan_config_param.return_value = \
                array.array('B', [10, 0, 1, 224])
        self.assertEqual(self.lib.get_lan_interface_ip_address(1),
                '10.0.1.224')

    def test_set_ip_address(self):
        self.lib.set_lan_interface_ip_address(1, '10.0.1.2')
        self.ipmi.set_lan_config_param.assert_called_once_with(1,
                pyipmi.lan.LAN_PARAMETER_IP_ADDRESS,
                array.array('B', [10, 0, 1, 2]))

    def test_mac_address_set_and_get_use_the_same_order(self):
        for kw in ('mac_address', 'gateway_mac_address'):
            self.ipmi.reset_mock()
            getattr(self.lib, 'set_lan_interface_' + kw)(1,
                    '00:11:22:33:44:55')
            data = self.ipmi.set_lan_config_param.call_args[0][2]
            self.ipmi.get_lan_config_param.return_value = data
            self.assertEqual(getattr(self.lib, 'get_lan_interface_' + kw)(1),
                    '00:11:22:33:44:55')


class TestSdr(LibraryTestCase):
    def setUp(self):
        super().setUp()
        self.sdr = mock.Mock(device_id_string='CPU Temp', number=1)
        self.sdr.convert_sensor_raw_to_value.return_value = 37.0
        self.lib._cp['prefetched_sdr_list'] = [self.sdr]
        self.ipmi.get_sensor_reading.return_value = (37, None)

    def test_sensor_reading_should_be_equal(self):
        self.lib.sensor_reading_should_be_equal('CPU Temp', '37')
        with self.assertRaises(AssertionError):
            self.lib.sensor_reading_should_be_equal('CPU Temp', '38')

    def test_selected_sdr_sensor_reading_should_be_equal(self):
        self.lib.select_sdr_by_name('CPU Temp')
        self.lib.selected_sdr_sensor_reading_should_be_equal('37')

    def test_selected_sdr_is_per_connection(self):
        self.lib.select_sdr_by_name('CPU Temp')
        self.lib._active_connection = IpmiConnection(self.ipmi, None)
        with self.assertRaisesRegex(AssertionError, 'No SDR selected'):
            self.lib.selected_sdr_name_should_be_equal('CPU Temp')

    def test_select_sdr_by_unknown_record_type(self):
        with self.assertRaises(AssertionError):
            self.lib.select_sdr_by_record_type('Full Sensor Record')

    def test_partial_add_sdr(self):
        self.lib.partial_add_sdr(0, 0, 0, 0, '0x01 0x02')
        self.ipmi.partial_add_sdr.assert_called_once_with(0, 0, 0, 0,
                array.array('B', [1, 2]))


class TestSel(LibraryTestCase):
    def test_no_sel_record_selected(self):
        with self.assertRaisesRegex(AssertionError, 'No SEL record selected'):
            self.lib.get_sensor_number_from_selected_sel_record()

    def test_select_unknown_record_id(self):
        self.lib._cp['prefetched_sel_records'] = [mock.Mock(record_id=1)]
        with self.assertRaises(AssertionError):
            self.lib.select_sel_record_by_record_id(2)


class TestFru(LibraryTestCase):
    def test_read_fru_data(self):
        self.ipmi.read_fru_data.return_value = b'\x01\x02'
        self.assertEqual(self.lib.read_fru_data(0, 2), [1, 2])

    def test_fru_data_tlv_text(self):
        self.lib._cp['prefetched_fru_data'] = {0: b'\xc3abc'}
        self.lib.fru_data_tlv_at_offset_should_be(0, 'ASCII OR UTF16', 3,
                'abc')

    def test_write_fru_data(self):
        self.lib.write_fru_data(0, '0x01 0x02')
        self.ipmi.write_fru_data.assert_called_once_with(
                array.array('B', [1, 2]), 0, 0)


class TestBmc(LibraryTestCase):
    def test_i2c(self):
        self.lib.i2c_write_read(0, 0, 0, '0xa0', 1, '0x01 0x02')
        self.lib.i2c_write(0, 0, 0, '0xa0', '0x01', '0x02')
        self.lib.i2c_read(0, 0, 0, '0xa0', 2)
        self.assertEqual(self.ipmi.i2c_write_read.call_args_list, [
            mock.call(0, 0, 0, 0xa0, 1, array.array('B', [1, 2])),
            mock.call(0, 0, 0, 0xa0, 0, array.array('B', [1, 2])),
            mock.call(0, 0, 0, 0xa0, 2, array.array('B')),
        ])


class TestPicmg(LibraryTestCase):
    def test_led_state_should_be(self):
        led = pyipmi.picmg.LedState()
        led.lamp_test_enabled = False
        led.override_enabled = True
        self.ipmi.get_led_state.return_value = led
        self.lib.get_fru_led_state(0, 0)
        self.lib.led_state_should_be('Override')
        with self.assertRaises(AssertionError):
            self.lib.led_state_should_be('Local Control')

    def test_get_signaling_class(self):
        self.ipmi.get_signaling_class.return_value = 0
        self.assertEqual(self.lib.get_signaling_class('FABRIC', 1), 0)

    def test_hotswap_sdr_not_prefetched(self):
        with self.assertRaisesRegex(AssertionError, 'not found'):
            self.lib.get_hotswap_state('PICMG Front Board:0')


class TestHpm(LibraryTestCase):
    def test_image_header_value(self):
        image = mock.Mock()
        image.header.foo = 'x'
        self.ipmi.open_upgrade_image.return_value = image
        self.lib.hpm_image_header_value_should_be('file', 'foo', 'x')


if __name__ == '__main__':
    unittest.main()
