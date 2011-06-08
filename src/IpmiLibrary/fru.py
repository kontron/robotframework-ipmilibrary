#
# Kontron IpmiLibrary
#
# author: Michael Walle <michael.walle@kontron.com>
# author: Heiko Thiery <heiko.thiery@kontron.com>
#

from robot.utils import asserts

from utils import int_any_base
from mapping import *

class Fru:
    def __init__(self, ipmi):
        self._fru_data = None

    def fetch_fru_data(self, fru_id=0):
        """Fetches the FRU data of the given `fru_id`.

        Fetching the FRU data is required for all further operation on the FRU
        data.
        """
        ac = self._active_connection
        ac._fru_data = ac._ipmi.read_fru_data(fru_id)

    def fru_data_byte_at_offset_should_be(self, offset, value, msg=None):
        """Fails if the FRU data does not contain `value` at the given `offset`
        """
        ac = self._active_connection
        offset = int_any_base(offset)
        value = int_any_base(value)

        if ac._fru_data is None:
            self.fetch_fru_data()

        asserts.fail_unless_equal(value, ord(ac._fru_data.raw[offset]), msg)

    def fru_data_bytes_at_offset_should_be(self, offset, length,
                value_expected, msg=None, order='lsb'):
        """Fails if the FRU data does not contain `value` at the given `offset`
        """
        ac = self._active_connection
        offset = int_any_base(offset)
        length = int_any_base(length)
        value_expected = int_any_base(value_expected)

        if ac._fru_data is None:
            self.fetch_fru_data()

        value = 0
        if order == 'lsb':
            for v in ac._fru_data.raw[offset+length-1:offset-1:-1]:
                value = (value << 8) + ord(v)
        elif order == 'msb':
            for v in ac._fru_data.raw[offset:offset+length]:
                value = (value << 8) + ord(v)
        else:
            raise RuntimeError('Unknown order')

        asserts.fail_unless_equal(value_expected, value, msg)

    def fru_data_tlv_at_offset_should_be(self, offset, expected_type,
                expected_length, expected_value, msg=None):
        ac = self._active_connection
        offset = int_any_base(offset)
        expected_type = find_fru_field_type_code(expected_type)
        expected_length = int_any_base(expected_length)

        if ac._fru_data is None:
            self.fetch_fru_data()

        type = (ord(ac._fru_data.raw[offset]) & 0xc0) >> 6
        asserts.fail_unless_equal(expected_type, type, 'type missmatch')

        length = ord(ac._fru_data.raw[offset]) & 0x3f
        asserts.fail_unless_equal(expected_length, length, 'length missmatch')

        value = None
        if expected_type == 0:
            expected_value = int_any_base(expected_value)
            slice = ac._fru_data.raw[offset+1:offset+length+1]
            value = 0
            for v in slice:
                value = (value << 8) + ord(v)
        elif expected_type == 3:
            value = ac._fru_data.raw[offset+1:offset+length+1]
        else:
            raise RuntimeError('type %s not supported' % expected_type)

        asserts.fail_unless_equal(expected_value, value, 'value missmatch')
