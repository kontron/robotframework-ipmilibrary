#!/usr/bin/env python

from setuptools import setup
import sys
sys.path.insert(0, 'src')

def main():
    setup(name = 'robotframework-ipmilibrary',
            version = '0.1',
            description = 'IPMI Library for Robot Framework',
            author_email = 'michael.walle@kontron.com',
            package_dir = { '' : 'src' },
            license = 'Apache License 2.0',
            classifiers = [
                'Development Status :: 4 - Beta',
                'Framework :: Robot Framework',
                'License :: OSI Approved :: Apache Software License',
                'Operating System :: OS Independent',
                'Programming Language :: Python',
                'Topic :: Software Development :: Testing',
            ],
            packages = [ 'IpmiLibrary' ],
            install_requires = [ 'robotframework', 'python-ipmi' ]
    )

if __name__ == '__main__':
    main()
