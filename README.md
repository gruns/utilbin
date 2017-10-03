# Utilbin

Utilbin is a collection of utilities to improve developer's lives.

The goal of utilbin is threefold:

  1. Be a central, welcoming community where everyone can collate and improve
     development tools together, all under a liberal license.

  2. Provide programmatic access to hosted utilities over a simple REST
     interface.

  3. Build in-browser (e.g. Javascript or WebAssembly) versions of every utility
     for local use, like with sensitive data that can't leave corporate
     firewalls.


### Getting Started

To run Utilbin locally, first checkout Utilbin.

```console
git clone https://github.com/gruns/utilbin.git
```

Next, install Utilbin's Python dependencies

```console
pip install furl curio flask docopt
```

Finally, install Utilbin's build dependencies: a C/C++ compiler toolchain,
[Emscripten](https://github.com/kripken/emscripten) (a toolchain that compiles C
and C++ to Javascript), and [browserify](http://browserify.org/) (a Javascript
bundler).

On Debian machines, install the C/C++ compiler toolchain with

```console
apt install build-essential
```

To install Emscripten, follow Emscripten's installation instructions here:

  * https://kripken.github.io/emscripten-site/docs/getting_started/downloads.html

Installation of Emscripten on Linux/OS X will look similar to

```console
$ wget https://s3.amazonaws.com/mozilla-games/emscripten/releases/emsdk-portable.tar.gz
$ tar xf emsdk-portable.tar.gz
$ cd emsdk-portable/
$ ./emsdk update
$ ./emsdk install latest
$ ./emsdk activate latest
$ ln -s "$(find $(pwd) -type f -name 'emcc')" /somewhere/in/your/path/emcc
```

Install browserify with

```console
npm install -g browserify
```


### Build the Utilities

With Utilbin checked out and the build dependencies installed, it's time to
build some utilities. Individual utilities can be built with

```console
./utilbind build <utility> [web | native]
```

To build every utility, for both web and native, run

```console
./utilbind build all
```


### Run Utilbin

Individual utilities can be run via utilbind's Command Line Interface (CLI) with

```console
./utilbind run <utility> <utility-args>
```

For example, to generate a random password, run

```console
$ ./utilbind run password_generator --length=20
ratipatawojorokepafu
```

In addition to providing a CLI to build and run utilities, utilbind is also an
HTTP daemon that can listen for, and serve, RESTrequests. To start the REST
server in listen mode (non-daemonizedd server mode), run

```console
./utilbind
Listening for requests on http://127.0.0.1:4337/...
...
```

And request away

```console
$ curl "http://localhost:4337/password_generator?length=20"
nawibolaxoqoriyatade
```


### Run Utilbin's Frontend Web Server

Once web versions of the utilities have been built (e.g. with `./utilbind build
all web`), start the frontend web server with

```
$ ./www.py
 * Running on http://127.0.0.1:5050/ (Press CTRL+C to quit)
 * Restarting with stat
 ...
```

and load [http://127.0.0.1:5050/](http://127.0.0.1:5050/) in your browser.


### Add a new Utility

To add a new utility to Utilbin, follow the [Add Utility](Add_Utility.md)
instructions and submit a pull request.
