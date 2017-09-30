# Add a utility to Utilbin

This document provides step-by-step instructions on how to add a new, example
utility to Utilbin. For the example utility, we'll create a straightforward echo
utility that simply mirrors any input it receives; send it 'hi', get 'hi'
back. We'll call this little utility 'echo'.


### Create Parent Directory

First, create a new `echo/` directory under the `utilities/` directory. All
utilities live in their own directory in the `utilities/` parent directory.

```shell
$ cd utilities/
$ mkdir echo
$ cd echo/
```

The name of the directory matters, as the directory name is also the URL path at
which the utility becomes accessible on utilbin.com, both in the GUI at
`http://utilbin.com/u/<directory name>` and via the REST interface at
`http://utilbin.com/<directory name>`. For example, the echo utility in the
`utilities/echo/` directory will become available at
`http://utilbin.com/u/echo/` (GUI) and `http://utilbin.com/echo/` (REST API).

### Python Utility Class

In the new `echo/` directory, create a new, blank Python file named
`echo.py`. This Python file will define the behavior and build processes of the
echo utility.

```shell
$ touch echo.py
$ $EDITOR echo.py
```

The name of this Python file, `echo.py`, doesn't matter -- it will be loaded by
utilbind through the package file `utilities/echo/__init__.py`, which we'll
create and configure later.

In `echo.py`, we need to declare a Python subclass of the `Utility` class, which
is defined in `utilbin/utilities/utility.py`. `TextUtility`, also a subclass of
the `Utility` class, is a useful, pre-defined base class to subclass instead of
`Utility` for text utilities, like echo. `TextUtility` automatically handles
encoding and decoding input and output to UTF8.

Next, fill echo.py with these contents:

```python
# -*- coding: utf-8 -*-

# Copyright _!_
#
# License _!_
#
# Original author: [Your name here]

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
```

Let's step through this file to examine the key pieces.


### Usage

`Echo.usage` is a multiline [docopt](http://docopt.org/) string that defines the
utility's usage across every interface: the web GUI
(`http://utilbin.com/u/echo`), the REST API (`http://utilbin.com/echo`), and the
CLI (`./utilbind run echo`).

Below, between curly braces (`{` and `}`), are the fields extracted from the
docopt usage string by utilbind.

```python
USAGE = """{Human Readable Utility Name}

Usage:
  ignored {action1} {[INPUT]}
  ignored {action2} {[INPUT]} {[options]}

Options:
  {-o, --option   Option text.}
"""
```

The first line, `{Human Readable Utility Name}` is the human-readable display
name of the utility. This display name is displayed to humans, like in the web
GUI's HTML. For the echo utility, this display name is `Echo`.

Each line under `Usage:` declares the actions available to this utility and the
options those actions take. A utility can have multiple actions, like 'encode'
and 'decode' for a codec, or only one action, like 'generate' for a password
generator. Every utility needs at least one action.

The `[INPUT]` positional argument is a special positional argument that
indicates this utility takes input. If `[INPUT]` is omitted, like in

```
Usage:
  util action [--option]
```

then no <textarea> input box will be presented in the web GUI and no input data
will be accepted via the REST API or CLI. Utilities without the `[INPUT]`
positional argument usually generate, not process, data. Examples include
password generators, UUID generators, etc.

Options enumerated under `Options:` are made available in the web GUI, REST API,
and CLI. For example

```
Usage:
  password_generator generate [--length <length>]

Options:
  -l <length>, --length=<length>  Password length, in characters [default: 16].
```

adds the `-l` and `--length` options.

```
$ curl http://utilbin.com/password_generator/generate?l=5
caluq
```

```
$ ./utilbind run password_generator generate --length=5
bazut
```

`[options]` is docopt shortcut option which means all options under `Options:`.

  > "[options]" is a shortcut that allows to avoid listing all options (from
  > list of options with descriptions) in a pattern.


### Utility Subclass

The `TextUtility` parent class defines the metadata and build behavior of the
utility.

```
from ..utility import Category, TextUtility

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
```

Here are the important attributes and methods:

  - `usage` is the docopt usage string.

  - `nativeExecutable` is the name of the native executable, built in
    `_buildNativeDistribution()`, run via the REST API and utilbin's CLI.

  - `category` is the appropriate enumeration value to categorize this app. The
    utility is displayed under this category in the web GUI.

  - `browserJSFiles` is a list of all the Javascript files this utility needs to
    run in the browser. These Javascript files are often built (e.g. with
    emscripten) or bundled (e.g. with browserify, webpack, etc) in
    `_buildWebDistribution()`.

  - `_buildWebDistribution()` and `_buildNativeDistribution()` are the methods
    run to build the native executable(s) and web assets for the utility. These
    methods are run via `./utilbind build [...]` to build and package utilities.

See the `Utility` base class in `utilbin/utilities/utility.py` for more
details. The attributes and methods above are the basics and suffice for simple
utilities. TODO(grun): Link to the `Utility` base class from this markdown
document.


### \__init\__.py

With echo.py complete, it's time to turn the now-complete echo utility into a
Python module and and connect it to utilbind.

To do so, create a \__init__.py package file in the `echo/` directory with the
contents:

```python
# -*- coding: utf-8 -*-

# Copyright _!_
#
# License _!_
#
# Original author: [Your name here]

from .echo import Echo

Utility = Echo
```

The key piece of this \__init__.py file is the `Utility` attribute, through
which the echo utility is exported. In this manner, utilbind can discover,
import, and use the new echo utility.


### Final testing

With the `echo/` complete, it's time to build and test the utility. Build the
web version with

```console
$ utilbind build echo web
```

and the native version with

```console
$ ./utilbind build echo native
```

Both can be built with

```console
$ ./utilbind build echo
```

Once built, test the echo utility via utilbin's CLI.

```console
$ ./utilbind run echo mirror sup
sup
```

Via the REST API.

```console
$ curl -d "sup" http://127.0.0.1:4337/echo/mirror
sup
```

And via the web GUI.

  * http://127.0.0.1:5050/u/echo

And that's it. Congratulations! You've successfully added a utility, with both
web and native versions, to utilbin.