# -*- coding: utf-8 -*-

# Copyright _!_
#
# License _!_
#
# Original author: Ansgar Grunseid

import subprocess
from glob import glob

from ..utility import Category, TextUtility

USAGE = """Base64 Codec

Usage:
  base64 encode [INPUT]
  base64 decode [INPUT]

Options:
  -h --help    Show this help information.
"""

class Base64Codec(TextUtility):
    usage = USAGE
    category = Category.CODEC
    nativeExecutable = 'base64codec'
    browserJSFiles = ['base64codec.out.js', 'base64codec-www.js']

    def _buildWebDistribution(self):
        srcfiles = ' '.join(glob('*.c'))
        exported = ['_encodeStr', '_decodeStr']
        cmd = (
            f'emcc -O3 --closure 0 --memory-init-file 0 {srcfiles} '
            f'-o base64codec.out.js -s EXPORTED_FUNCTIONS="{exported}"')
        subprocess.run(cmd, shell=True, check=True) # Raises CalledProcessError.

        #b64js = pjoin(self.dirpath, 'base64codec.js')
        #with open('a', 'w') as a, open('b', 'w') as b:
        #  shutil.copyfileobj(...)

    def _buildNativeDistribution(self):
        srcfiles = ' '.join(glob('*.c'))
        cmd = f'cc {srcfiles} -o {self.nativeExecutable}'
        subprocess.run(cmd, shell=True, check=True) # Raises CalledProcessError.
