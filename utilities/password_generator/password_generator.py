# -*- coding: utf-8 -*-

# Copyright _!_
#
# License _!_
#
# Original author: Ansgar Grunseid

import subprocess
from os.path import dirname, join as pjoin

from ..utility import Category, TextUtility

# TODO(grun): Add more password generation options, like:
#
#  -s --no-symbols     Exclude symbols '@#$%'.
#  -n --no-numbers     Exclude numbers '0123456789'.
#  -u --no-uppercase   Exclude uppercase characters 'A..Z'.
#
USAGE = """Password Generator

Usage:
  password generate [options]

Options:
  -l <length>, --length=<length>   Password length, in characters [default: 16].
  -h --help                        Show this help information.
"""

class PasswordGenerator(TextUtility):
    usage = USAGE
    category = Category.GENERATOR
    nativeExecutable = 'passgen-cli.js'
    browserJSFiles = ['passgen.bundle.js']

    def _buildWebDistribution(self):
        cmd = f'browserify passgen-www.js -o passgen.bundle.js'
        subprocess.run(cmd, shell=True, check=True) # Raises CalledProcessError.
                         
