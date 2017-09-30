# -*- coding: utf-8 -*-

# Copyright _!_
#
# License _!_
#
# Original author: Ansgar Grunseid

import subprocess

from ..utility import Category, TextUtility

USAGE = """Echo

Usage:
  echo mirror [INPUT]

Options:
  -h --help    Show this help information.
"""

class Echo(TextUtility):
    usage = USAGE
    nativeExecutable = 'echo'
    category = Category.MISCELLANEOUS
    browserJSFiles = ['echo.out.js', 'echo-www.js']

    def _buildWebDistribution(self):
        exported = ['_mirror']
        cmd = (
            f'emcc -O3 --closure 0 --memory-init-file 0 echo.c '
            f'-o echo.out.js -s EXPORTED_FUNCTIONS="{exported}"')
        subprocess.run(cmd, shell=True, check=True) # Raises CalledProcessError.

    def _buildNativeDistribution(self):
        cmd = f'cc echo.c -o {self.nativeExePath}'
        subprocess.run(cmd, shell=True, check=True) # Raises CalledProcessError.
