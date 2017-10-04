# -*- coding: utf-8 -*-

# Copyright _!_
#
# License _!_
#
# Original author: Ansgar Grunseid

import os
import sys
import stat
from abc import ABC
from enum import Enum
from contextlib import contextmanager
from os.path import isfile, dirname, basename, join as pjoin

@contextmanager
def changeDirectory(path):
    saved = os.getcwd()
    os.chdir(path)
    yield
    os.chdir(saved)

def makeExecutable(fpath):
    # Make <fpath> executable for users who already have read access. See
    # https://stackoverflow.com/a/30463972.
    mode = os.stat(fpath).st_mode
    mode |= (mode & 0o444) >> 2
    os.chmod(fpath, mode)


class Category(Enum):  # Attribute value is the category name displayed in HTML.
    CODEC = 'Codecs'
    GENERATOR = 'Generators'
    MISCELLANEOUS = 'Miscellaneous'


class Utility(ABC):
    """
    Provide a generic interface to run various utilities, which have
    wildly different requirements for their languages, runtimes, setup,
    dependencies, etc.

    Every utility needs to subclass this class.
    """
    usage = None
    browserJSFiles = []  # All required JS files for browsers. Order preserved.
    category = Category.MISCELLANEOUS
    nativeExecutable = 'Undefined Native Executable'  # Native executable name.

    def setup(self):
        pass

    def processArguments(self, args, kwargs):
        return args, kwargs

    def processOutput(self, stdout, stderr):
        return stdout, stderr  # Passthrough.

    def teardown(self):
        pass

    def buildWebDistribution(self):
        with changeDirectory(self.dirpath):
            self._buildWebDistribution()  # Implemented by subclass.
            # TODO(grun): Minify the JS assets (with Closure Compiler?) if
            # they're not already minified.
            #for js in browserJSFiles:
            #    self.minifyJS(js)

    def buildNativeDistribution(self):
        with changeDirectory(self.dirpath):
            self._buildNativeDistribution()  # Implemented by subclass.
        makeExecutable(self.nativeExePath)

    def isWebReady(self):
        return all(isfile(f) for f in self.browserJSPaths)

    def isNativeReady(self):
        return os.access(self.nativeExePath, os.X_OK)

    # TODO(grun): Change the <name> and <displayName> variable names to better
    # describe their purpose. displayName is apt enough; just 'name' is
    # not. codename? varname?
    @property
    def name(self):
        return basename(self.dirpath)

    @property
    def displayName(self):
        # Readable English name to be displayed to humans in HTML, etc.
        return self.usage.splitlines()[0].strip()

    @property
    def nativeExePath(self):
        return pjoin(self.dirpath, self.nativeExecutable)

    @property
    def browserJSPaths(self):
        return [pjoin(self.dirpath, f) for f in self.browserJSFiles]

    @property
    def dirpath(self):
        # Path to this utility's directory. Access the subclass's __file__
        # attribute to construct the path to the subclass's directory, not this
        # abstract base class's directory.
        subclass = sys.modules[self.__module__]
        return dirname(subclass.__file__)

    # The _buildWebDistribution() and _buildNativeDistribution() methods should
    # only use the standard library for concurrency and subprocess management
    # to decouple the concurrency management used in utilbind (e.g. curio) from
    # requirements to build and use individual utilities. If, in the future,
    # this decoupling only proves a hindrance, like to build multiple tools in
    # parallel, re-examine this restriction.
    def _buildWebDistribution(self):
        pass

    def _buildNativeDistribution(self):
        pass


class TextUtility(Utility):
    _encoding = 'utf8'

    def processOutput(self, stdout, stderr):
        stdout = stdout.decode(self._encoding)
        stderr = stderr.decode(self._encoding)
        return stdout, stderr
