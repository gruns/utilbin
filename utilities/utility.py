# -*- coding: utf-8 -*-

# Copyright _!_
#
# License _!_
#
# Original author: Ansgar Grunseid

import os
import sys
import stat
from enum import Enum
from abc import abstractmethod
from contextlib import contextmanager
from os.path import dirname, basename, join as pjoin

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


class Utility:
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

    @abstractmethod
    def setup(self):
        pass

    @abstractmethod
    def processArguments(self, args, kwargs):
        return args, kwargs

    @abstractmethod
    def processOutput(self, stdout, stderr):
        return stdout, stderr  # Passthrough.

    @abstractmethod
    def teardown(self):
        pass

    def buildWebDistribution(self):
        with changeDirectory(self.dirpath):
            self._buildWebDistribution()  # Implemented by subclass.

    def buildNativeDistribution(self):
        with changeDirectory(self.dirpath):
            self._buildNativeDistribution()  # Implemented by subclass.
        makeExecutable(self.nativeExePath)

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
    # parallel, re-examine this decision.
    @abstractmethod
    def _buildWebDistribution(self):
        pass

    @abstractmethod
    def _buildNativeDistribution(self):
        pass


class TextUtility(Utility):
    _encoding = 'utf8'

    def processOutput(self, stdout, stderr):
        stdout = stdout.decode(self._encoding)
        stderr = stderr.decode(self._encoding)
        return stdout, stderr