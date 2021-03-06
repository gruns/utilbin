# Add a utility to Utilbin

This document provides step-by-step instructions on how to add a new utility to
Utilbin via a simple example utility. For the example utility, we'll create a
utility that simply mirrors any input it receives; send it 'hi', get 'hi'
back. We'll call this little utility 'echo'.


### Create Parent Directory

First, create a new `echo/` directory under the `utilbin/utilities/`
directory. All utilities live in their own directory in the `utilbin/utilities/`
parent directory.

```console
$ cd utilities/
$ mkdir echo
$ cd echo/
```

The name of this directory matters: this directory name is also the URL path at
which the utility becomes accessible on utilbin.com, both in the GUI at
`http://utilbin.com/u/<directory name>` and via the REST interface at
`http://utilbin.com/<directory name>`. For example, the echo utility in the
`utilbin/utilities/echo/` directory will become available at
`http://utilbin.com/u/echo/` (GUI) and `http://utilbin.com/echo/` (REST API).


### Utility

For the echo utility itself, all the utility needs to do is read from stdin and
write to stdout. A simple C program will suffice. In the new `echo/` directory,
create a new C file named `echo.c` with the contents:

```c
// Copyright _!_
//
// License _!_
//
// Original author: [Your name here]

#include <stdio.h>
#include <string.h>

#define BUFSIZE 65536

int mirror(char *s, char *outbuf) {
  strcpy(outbuf, s);
  return strlen(s);
}

int main(int argc, char **argv) {
  if (argc < 2 || argc > 3 || !!strcmp(argv[1], "mirror"))
    return -1;

  int nbytes;
  char buf[BUFSIZE];
  if (argc == 3)
    printf("%s", argv[2]);
  else
    while (!feof(stdin))
      if ((nbytes = fread(buf, 1, BUFSIZE, stdin)) >= 0 && !ferror(stdin))
        fprintf(stdout, buf, nbytes);

  return 0;
}
```

All utilities must read from stdin and write to stdout. utilbind spawns
utilities, like echo, as subprocesses and communicates with them over the
standard streams stdin and stdout.

Beyond stdin and stdout, the `mirror()` function is independently declared so as
to be exported to Javascript by emscripten (more on that below).


### Python Utility Class

Also in the `utilities/echo/` directory, create a new Python file named
`echo.py`. This Python file will define the behavior and build processes of the
echo utility.

The name of this Python file, `echo.py`, doesn't matter -- it will be loaded by
utilbind through the Python package file `utilities/echo/__init__.py`, which
we'll create and configure later.

In `echo.py`, we need to declare a Python subclass of the `Utility` class, which
is defined in `utilbin/utilities/utility.py`. `TextUtility`, itself a subclass
of the `Utility` class, is a useful, pre-defined base class for text utilities,
like echo, that automatically handles encoding and decoding input and output to
UTF8.

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
utility's usage across every Utilbin interface: the web GUI
(`http://utilbin.com/u/echo`), the REST API (`http://utilbin.com/echo`), and the
CLI (`./utilbind run echo`).

Below, between curly braces (`{` and `}`), are the fields extracted from the
docopt usage string by utilbind.

```python
USAGE = """{Human Readable Utility Name}

Usage:
  utility {action1} {[INPUT]}
  utility {action2} {[INPUT]} {[options]}

Options:
  {-o, --option   Option text.}
"""
```

The first line, `{Human Readable Utility Name}` is the human-readable display
name of the utility. This display name is displayed to humans, like in the web
GUI's HTML. For the echo utility, this display name is the string `Echo`.

Each line under `Usage:` defines the actions available to this utility and the
options available to those actions. A utility can have multiple actions, like
'encode' and 'decode' for a codec, or only one action, like 'generate' for a
password generator. Every utility needs at least one action.

The `[INPUT]` positional argument is a special positional argument that
indicates this utility takes input. If `[INPUT]` is omitted, like in

```
Usage:
  utility action [--option]
```

then no <textarea> input box will be presented in the web GUI and no input data
will be accepted via the CLI or REST API. Utilities without the `[INPUT]`
positional argument usually generate, not process, data. Examples include
password generators, UUID generators, etc.

Options enumerated under `Options:` are made available in the web GUI, CLI, and
REST API. For example

```
Usage:
  password_generator generate [--length <length>]

Options:
  -l <length>, --length=<length>  Password length, in characters [default: 16].
```

adds the `-l` and `--length` options to the `generate` action.

```console
$ curl http://utilbin.com/password_generator/generate?l=5
caluq
```

```console
$ ./utilbind run password_generator generate --length=5
bazut
```

`[options]` is a docopt shortcut option which means all options under
`Options:`.

  > "[options]" is a shortcut that allows to avoid listing all options (from
  > list of options with descriptions) in a pattern.

See the [docopt documentation](http://docopt.org/) for more details on docopt
usage strings.


### Utility Subclass

The `TextUtility` parent class defines the metadata, behavior, and build steps
of the utility.

```python
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

  - `usage` is the [docopt](http://docopt.org/) usage string.

  - `nativeExecutable` is the name of the native executable, built in
    `_buildNativeDistribution()`, spawned as a subprocess by utilbin.

  - `category` is the appropriate enumeration value to categorize this
    utility. The utility is organized under this category in the web GUI.

  - `browserJSFiles` is a list of all the Javascript files this utility needs to
    run in the browser. These Javascript files are often built, like with
    emscripten, or bundled, like with browserify, in `_buildWebDistribution()`.

  - `_buildWebDistribution()` and `_buildNativeDistribution()` build the
    utility's native executable(s) and web assets, respectively. These methods
    are run via `./utilbind build [...]` command.

See the `Utility` base class in `utilbin/utilities/utility.py`
[here](utilities/utility.py) for more details. The attributes and methods above
are the basics and suffice for simple utilities.


### \_\_init\_\_.py

With echo.py complete, it's time to turn the `echo/` directory into a Python
module and connect it to utilbind.

To do so, create a \_\_init\_\_.py file in the `echo/` directory with the
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

The key piece of this \_\_init\_\_.py file is the `Utility` attribute, through
which the `Echo` utility is exported. In this manner, utilbind can discover,
import, and use your new echo utility.


### Final testing

The `echo/` directory is now replete. It's time to build and test the
utility. Build both the web version and the native version with

```console
$ utilbind build echo
```

Once built, test the native version via utilbin's CLI.

```console
$ ./utilbind run echo mirror sup
sup
```

Then via the REST API.

```console
$ curl -d "input=sup" http://127.0.0.1:4337/echo/mirror
sup
```

And finally via the web GUI.

  * http://127.0.0.1:5050/u/echo

And that's it. Congratulations! You've successfully added a utility, with both
web and native versions, to Utilbin.