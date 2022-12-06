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

import array

from robot.utils import asserts
import pyipmi

from .utils import int_any_base
from .mapping import *

class Fru:
    def _fru_data(self, fru_id):
        if ('prefetched_fru_data' in self._cp
                and fru_id in self._cp['prefetched_fru_data']):
            return self._cp['prefetched_fru_data'][fru_id]
        else:
            return self._ipmi.read_fru_data(fru_id=fru_id)

    def prefetch_fru_data(self, fru_id=0):
        """Fetches the FRU data of the given `fru_id`.

        After prefetching the FRU data, all further operations will use this
        cached data. Note that every connection has its own cache.
        """

        fru_id = int(fru_id)
        if 'prefetched_fru_data' not in self._cp:
            self._cp['prefetched_fru_data'] = {}
        self._cp['prefetched_fru_data'][fru_id] = \
                self._ipmi.read_fru_data(fru_id=fru_id)

    def get_fru_inventory_area_size(self, fru_id=0):
        """Returns the FRU Inventory Area Info size.
        """
        fru_id = int_any_base(fru_id)
        return self._ipmi.get_fru_inventory_area_info(fru_id)



    def read_fru_data(self, offset, count, fru_id=0):
        """Reads data bytes from FRU data area.

        `offset`
        `count`
        `fru_id`
        """
        fru_id = int(fru_id)
        offset = int_any_base(offset)
        count = int_any_base(count)
        data_string = self._ipmi.read_fru_data(offset, count, fru_id)
        data = [ord(c) for c in data_string]
        return data

    def write_fru_data(self, offset, data, fru_id=0):
        """Writes data bytes to FRU data area.

        `offset`
        `data`
        `fru_id`
        """

        fru_id = int(fru_id)
        offset = int_any_base(offset)
        if isinstance(data, basestring):
            data = [int_any_base(d) for d in data.split(' ')]
        elif isinstance(data, list):
            data = data
        else:
            data = [int_any_base(data)]
        data = array.array('B', data)
        self._ipmi.write_fru_data(data, offset, fru_id)

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

        asserts.assert_equal(expected_data, data, msg)

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

        asserts.assert_equal(expected_type, (tlv[0] >> 6) & 0x3, msg)
        asserts.assert_equal(expected_length, tlv[0] & 0x3f, msg)
        asserts.assert_equal(expected_data, tlv[1:], msg)

    def fru_data_get_inventory(self, fru_id=0):
        """Return the Fru Data for the given fru_id.
        """
        fru_id = int_any_base(fru_id)
        return self._fru_data(fru_id)

    def fru_data_get_board_manufacturer(self, fru_id=0):
        """Returns the Board Manufacturer.
        """
        fru_id = int_any_base(fru_id)
        fru = pyipmi.fru.FruInventory(self._fru_data(fru_id))
        return str(fru.board_info_area.manufacturer)

    def fru_data_board_manufacturer_should_be(self, expected_value, fru_id=0):
        """Fails if the Board Manufacturer is not as expected.
        """
        value = self.fru_data_get_board_manufacturer(fru_id)
        asserts.assert_equal(expected_value, value)

    def fru_data_get_board_product_name(self, fru_id=0):
        """Returns the Board Product Name.
        """
        fru_id = int_any_base(fru_id)
        fru = pyipmi.fru.FruInventory(self._fru_data(fru_id))
        return str(fru.board_info_area.product_name)

    def fru_data_board_product_name_should_be(self, expected_value, fru_id=0):
        """Fails if the Board Product Name is not as expected.
        """
        value = self.fru_data_get_board_product_name(fru_id)
        asserts.assert_equal(expected_value, value)

    def fru_data_get_board_serial_number(self, fru_id=0):
        """Returns the Board Serial Number.
        """
        fru_id = int_any_base(fru_id)
        fru = pyipmi.fru.FruInventory(self._fru_data(fru_id))
        return str(fru.board_info_area.serial_number)

    def fru_data_board_serial_number_should_be(self, expected_value, fru_id=0):
        """Fails if the Board Serial Number is not as expected.
        """
        value = self.fru_data_get_board_serial_number(fru_id)
        asserts.assert_equal(expected_value, value)

    def fru_data_get_board_part_number(self, fru_id=0):
        """Returns the Board Part Number.
        """
        fru_id = int_any_base(fru_id)
        fru = pyipmi.fru.FruInventory(self._fru_data(fru_id))
        return str(fru.board_info_area.part_number)

    def fru_data_board_part_number_should_be(self, expected_value, fru_id=0):
        """Fails if the Board Part Number is not as expected.
        """
        value = self.fru_data_get_board_part_number(fru_id)
        asserts.assert_equal(expected_value, value)

    def fru_data_get_product_manufacturer(self, fru_id=0):
        """Returns the Product Manufacturer.
        """
        fru_id = int_any_base(fru_id)
        fru = pyipmi.fru.FruInventory(self._fru_data(fru_id))
        return str(fru.product_info_area.manufacturer)

    def fru_data_product_manufacturer_should_be(self, expected_value, fru_id=0):
        """Fails if the Product Manufacturer is not as expected.
        """
        value = self.fru_data_get_product_manufacturer(fru_id)
        asserts.assert_equal(expected_value, value)

    def fru_data_get_product_name(self, fru_id=0):
        """Returns the Product Name.
        """
        fru_id = int_any_base(fru_id)
        fru = pyipmi.fru.FruInventory(self._fru_data(fru_id))
        return str(fru.product_info_area.name)

    def fru_data_product_name_should_be(self, expected_value, fru_id=0):
        """Fails if the Product Name is not as expected.
        """
        value = self.fru_data_get_product_name(fru_id)
        asserts.assert_equal(expected_value, value)

    def fru_data_get_product_part_number(self, fru_id=0):
        """Returns the Product Part Number.
        """
        fru_id = int_any_base(fru_id)
        fru = pyipmi.fru.FruInventory(self._fru_data(fru_id))
        return str(fru.product_info_area.part_number)

    def fru_data_product_part_number_should_be(self, expected_value, fru_id=0):
        """Fails if the Product Part Number is not as expected.
        """
        value = self.fru_data_get_product_part_number(fru_id)
        asserts.assert_equal(expected_value, value)

    def fru_data_get_picmg_multirecord_from_type(self, record_type, index=0, fru_id=0):
        """Returns the PICMG mulirecord specified by type.
        supported types are:
        `record_type`: Power Module Capability
        `index` specifies the index of the requested record.
        `fru_id`
        """
        record_type = find_picmg_multirecord_id(record_type)
        index = int_any_base(index)
        fru_id = int_any_base(fru_id)
        fru = pyipmi.fru.FruInventory(self._fru_data(fru_id))

        found_num = 0
        for record in fru.multirecord_area.records:
            if ((record.record_type_id, record.picmg_record_type_id) ==
                (pyipmi.fru.FruDataMultiRecord.TYPE_OEM_PICMG, record_type)):
                if found_num == index:
                    return record

        raise AssertionError('Record type %s index=%s not found for fru_id=%s'
                 % (record_type, index, fru_id))
