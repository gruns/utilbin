#!/usr/bin/env python3.6
# -*- coding: utf-8 -*-

# Copyright _!_
#
# License _!_
#
# Original author: Ansgar Grunseid

HELP = """
utilbind - Utility Bin Daemon

Usage:
  utilbind run <utility> [utility-options]

Options:
  --version    Show version.
  -h --help    Show this help information.
"""
UTILITY_TIMEOUT = 5  # Seconds.
UTILITIES_DIRECTORY = './utilities/'

import os
from subprocess import PIPE
from os.path import isfile, join as pjoin

import curio
from docopt import docopt
from curio import timeout_after, TaskTimeout
from curio.subprocess import CalledProcessError

async def runUtilityCLI(exe):
    success, stdout, stderr = await runUtility(exe)
    if success and None not in [stdout, stderr]:
        print(f'stdout: {stdout}')
        print
        print(f'stderr: {stderr}')

async def runUtility(exe):
    success, stdout, stderr = False, None, None

    try:
        async with timeout_after(UTILITY_TIMEOUT):
            proc = await curio.subprocess.run(exe, stdout=PIPE, stderr=PIPE)
    except TaskTimeout:
        print(f'Utility {exe} timed out after {UTILITY_TIMEOUT} seconds.')
    except CalledProcessError as e:
        print(f'Utility {exe} returned with non-zero retcode: {e.returncode}.')
    else:
        success = True
        # TODO(grun): Handle received data intelligently -- not all utility
        # output will be text (i.e. UTF-8), e.g. raw JPEG data.
        stdout, stderr = proc.stdout.decode('utf8'), proc.stderr.decode('utf8')

    return success, stdout, stderr

def checkForUtility(utility):
    exePath = pjoin(UTILITIES_DIRECTORY, utility, utility)
    exists = isfile(exePath)
    isExecutable = os.access(exePath, os.X_OK)
    return exePath, exists and isExecutable

def main():
    args = docopt(HELP)  # Raises SystemExit on unknown CLI args.

    if args.get('run'):  # Run utility via the CLI.
        utility = args.get('<utility>')
        exe, exists = checkForUtility(utility)
        if exe and exists:
            curio.run(runUtilityCLI, exe)
        else:
            print(f'Failed to find the utility "{utility}".')

if __name__ == '__main__':
    main()


