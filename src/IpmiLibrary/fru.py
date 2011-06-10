#
# Kontron IpmiLibrary
#
# author: Michael Walle <michael.walle@kontron.com>
# author: Heiko Thiery <heiko.thiery@kontron.com>
#

import array

from robot.utils import asserts
import pyipmi

from utils import int_any_base
from mapping import *

class Fru:
    def _fru_data(self, fru_id):
        if ('prefetched_fru_data' in self._cp
                and fru_id in self._cp['prefetched_fru_data']):
            return self._cp['prefetched_fru_data'][fru_id]
        else:
            return self._ipmi.read_fru_data(fru_id)

    def prefetch_fru_data(self, fru_id=0):
        """Fetches the FRU data of the given `fru_id`.

        After prefetching the FRU data, all further operations will use this
        cached data. Note that every connection has its own cache.
        """

        fru_id = int(fru_id)
        if 'prefetched_fru_data' not in self._cp:
            self._cp['prefetched_fru_data'] = {}
        self._cp['prefetched_fru_data'][fru_id] = self._fru_data(fru_id)

    def fru_data_at_offset_should_be(self, offset, expected_data, fru_id=0,
            msg=None):
        """Fails unless the FRU data contains the expected data at the given
        offset."""

        fru_id = int(fru_id)
        offset = int_any_base(offset)
        expected_data = [int_any_base(d) for d in expected_data.split(' ')]

        data = self._fru_data(fru_id)[offset:offset+len(expected_data)]

        # convert to common data structure
        data = array.array('B', data)
        expected_data = array.array('B', expected_data)

        asserts.fail_unless_equal(expected_data, data, msg)

    def fru_data_tlv_at_offset_should_be(self, offset, expected_type,
                expected_length, expected_data, fru_id=0, msg=None):
        """Fails unless the FRU data contains the TLV triplet at the given
        offset."""

        offset = int_any_base(offset)
        expected_type = find_fru_field_type_code(expected_type)
        expected_length = int_any_base(expected_length)
        fru_id = int(fru_id)

        # XXX: refactor this, pyipmi already has code for decoding TLVs
        if expected_type == 0:
            # binary
            expected_data = [int_any_base(d) for d in expected_data.split(' ')]
        else:
            expected_data = str(expected_data)
        expected_data = array.array('B', expected_data)

        tlv = array.array('B',
                self._fru_data(fru_id)[offset:offset+len(expected_data)+1])

        asserts.fail_unless_equal(expected_type, (tlv[0] >> 6) & 0x3, msg)
        asserts.fail_unless_equal(expected_length, tlv[0] & 0x3f, msg)
        asserts.fail_unless_equal(expected_data, tlv[1:], msg)
