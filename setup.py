#!/usr/bin/env python

from distutils.core import setup
import sys
sys.path.insert(0, 'src')


def main():
    setup(name         = 'robotframework-ipmilibrary',
          version      = '0.1',
          description  = 'IPMI Library for Robot Framework',
          author_email = 'michael.walle@kontron.com',
          package_dir  = { '' : 'src' },
          packages     = [ 'IpmiLibrary' ]
          )

if __name__ == '__main__':
    main()
