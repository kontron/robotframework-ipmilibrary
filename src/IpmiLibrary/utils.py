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

from robot.utils import normalizing

def find_attribute(obj, attr, prefix):
    attr = str(attr)
    for i_attr in dir(obj):
        normalized_i_attr = normalizing.normalize(i_attr, ignore='_')
        normalized_attr = normalizing.normalize(prefix + attr,
                ignore='_')
        if normalized_i_attr == normalized_attr:
            return getattr(obj, i_attr)

    try:
        attr = int(attr, 0)
        return attr
    except ValueError:
        raise RuntimeError('Attribute "%s" in "%s" not found.' % (attr, obj))

def int_any_base(i, base=0):
    try:
        return int(i, base)
    except TypeError:
        return i
    except ValueError:
        raise RuntimeError('Could not parse integer "%s"' % i)

def ip_address_to_string(ip_list, inverted=False):
    """Returns a IP address string.
    """
    fn = lambda x:x
    if inverted:
        fn = reversed
    return '.'.join(['%d' % b for b in fn(ip_list)])

def parse_ip_address(ip_address):
    """Converts a IP address string.

    Returns a quatruple in case of a IPv4 address.
    """
    ip = [int(v) for v in ip_address.split('.', 3)]
    return ip

def mac_address_to_string(mac_list, inverted=False):
    """Returns a MAC address string.
    """
    fn = lambda x:x
    if inverted:
        fn = reversed
    return ':'.join(['%02x' % b for b in fn(mac_list)])

def parse_mac_address(mac_address):
    """Converts a MAC address string.
    Returns a list containing the mac address bytes.
    """
    return [int(v,16) for v in reversed(mac_address.split(':', 5))]
