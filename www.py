#!/usr/bin/env python3.6
# -*- coding: utf-8 -*-

# Copyright _!_
#
# License _!_
#
# Original author: Ansgar Grunseid

import os
import re
import time
import os.path
from importlib.machinery import SourceFileLoader
from os.path import isdir, dirname, join as pjoin

import docopt
from flask import abort, Flask, render_template, send_from_directory

# Import utilbind dynamically. utilbind can't be imported with Python's
# standard import statement because it doesn't have a .py extension.
utilbind = SourceFileLoader('utilbind', './utilbind').load_module()

PORT = 5050
TIMESTAMP = int(time.time())

app = Flask(
    'Utilbin',
    static_folder = './www',
    static_url_path = '/static',
    template_folder = './www/templates')

def staticAssetPath(asset):
    name, ext = os.path.splitext(asset)
    #if not DEBUG and not name.lower().endswith('.min'):
    #    ext = f'.min{ext}' % ext
    return f'/static/{ext[1:]}/{asset}?ts={TIMESTAMP}'

def staticAssetPathsForUtility(util):
    return [f'/u/{util.name}/{f}' for f in util.browserJSFiles]

def getAllUtilitiesByCategory():
    byCategory = {}
    #for util in discoverAllUtilities(webReady=True):
    for util in utilbind.discoverAllUtilities():
        byCategory.setdefault(util.category.value, []).append(util)
    return byCategory

# Quick and dirty monkeypatching of docopt's Option parsing code to add option
# descriptions to Option objects.
#
# TODO(grun): Integrate description parsing into docopt directly and push these
# changes upstream so parsed, cleaned descriptions are available on Option
# objects in future docopt releases.
#
# parse_section() below was taken from the latest version of docopt on Github
# (https://github.com/docopt/docopt), which has yet to be published to PyPI.
def parse_section(name, source):
    pattern = re.compile(
        '^([^\n]*' + name + '[^\n]*\n?(?:[ \t].*?(?:\n|$))*)',
        re.IGNORECASE | re.MULTILINE)
    return [s.strip() for s in pattern.findall(source)]

def extractOptionDescription(line):
    _, _, description = line.strip().partition('  ')
    description = re.sub('\s*\[default: .*\]', '', description).strip()
    return description

def parseDocoptOptions(usage):
    defaults = []

    for s in parse_section('options:', usage):
        # FIXME corner case "bla: options: --foo"
        _, _, s = s.partition(':')  # get rid of "options:"
        split = re.split('\n[ \t]*(-\S+?)', '\n' + s)[1:]
        split = [s1 + s2 for s1, s2 in zip(split[::2], split[1::2])]

        # Modified from docopt {
        #options = [Option.parse(s) for s in split if s.startswith('-')]
        #defaults += options
        for line in split:
            if not line.startswith('-'):
                continue
            option = docopt.Option.parse(line)
            option.description = extractOptionDescription(line)  # Monkeypatch.
            defaults.append(option)
        # } End of modified from docopt.

    return defaults
#
# End of docopt monkeypatch hackery.
#

def optionToHTMLInputAttributes(option):
    # TODO(grun): Add or figure out a better way to determine the most
    # appropriate <option> type. See all <option> types here:
    #   https://developer.mozilla.org/en-US/docs/Web/HTML/Element/input
    print('option', repr(option))
    present = option.value not in [None, True, False]
    value = '' if not present else f' value="{option.value}"'
    name = option.long.lstrip('-') if option.long else option.short.lstrip('-')
    attrs = {
        'name': name,
        'description': option.description,  # See docopt monkeypatching above.
        'value': '' if not present else option.value,
        'long': option.long.lstrip('-') if option.long else None,
        'short': option.short.lstrip('-') if option.short else None,
        'type': 'number' if present and option.value.isdigit() else 'text',
        }
    return attrs

def usageToHTMLFormFields(usage):
    """
    Parse the Pattern tree returned by docopt.parse_pattern() into a
    dictionary that represents the HTML form fields for <usage>.
    Examples:

        Required(
          Required(
            Command('generate', False),
            Optional(AnyOptions())))
        
        {'encode': {'takesInput': False, 'options': [...]}}
  
        
        Required(
          Either(
            Required(
              Command('encode', False),
              Optional(Command('input', False))),
            Required(
              Command('decode', False),
              Optional(Command('input', False)))))
        
        {'encode': {'takesInput': True, 'options': []},
         'decode': {'takesInput': True, 'options': []}}
  
        
        Required(
          Either(
            Required(
              Command('encode', False),
              Optional(Command('input', False)),
              Optional(AnyOptions())),
            Required(
              Command('decode', False),
              Optional(Command('input', False)))))
        
        {'encode': {'takesInput': True, 'options': [...]},
         'decode': {'takesInput': True, 'options': []}}
    """
    d = docopt
    commands = {}

    allOptions = parseDocoptOptions(usage)
    patterns = d.parse_pattern(
        d.formal_usage(d.printable_usage(usage)), allOptions)

    # Remove --help and --version options.
    allOptions = [
        o for o in allOptions if
        o.short not in ['-h' '-v'] and o.long not in ['--help', '--version']]

    root = patterns
    if root.children and type(root.children[0]) in [d.Either, d.OneOrMore]:
        root = root.children[0]
        
    for node in root.children:
        if (type(node) is not d.Required or
                type(node.children[0]) is not d.Command):
            continue

        command = node.children[0]
        optionals = [c for c in node.children[1:] if type(c) is d.Optional]

        takesInput = any(
            type(o.children[0]) is d.Argument and o.children[0].name == 'INPUT'
            for o in optionals)

        if any(type(o.children[0]) is d.AnyOptions for o in optionals):
            cmdOptions = [
                optionToHTMLInputAttributes(o)
                for o in allOptions if type(o) not in [d.Command, d.Argument]]
        else:
            cmdOptions = [
                optionToHTMLInputAttributes(o) for optional in optionals
                for o in optional.children
                if type(o) not in [d.Command, d.Argument]]

        commands[command.name] = {
            'options': cmdOptions,
            'takesInput': takesInput,}

    return commands

@app.route('/')
def index():
    return render_template('index.html', vars=dict(
        title = 'UtilBin -- For Lizards Only',
        cssFiles = [staticAssetPath('utilbin.css')],
        utilsByCategory = getAllUtilitiesByCategory(),))

@app.route('/u/<name>')
def utility(name):
    util = utilbind.loadUtility(name)
    if not util:
        abort(404)  # Raises werkzeug.exceptions.NotFound.
    commands = usageToHTMLFormFields(util.usage)
    return render_template('utility.html', vars=dict(
        util = util,
        commands = commands,
        jsFiles = (
            [staticAssetPath('utilbin.js')] +
            staticAssetPathsForUtility(util)),
        title = f'UtilBin -- {util.displayName}',
        cssFiles = [staticAssetPath('utilbin.css')],
        utilsByCategory = getAllUtilitiesByCategory(),
        takesInput = any(d.get('takesInput') for d in commands.values())))

@app.route('/u/<name>/<filename>.js')
def utilityJavascriptAsset(name, filename):
    return send_from_directory(
        pjoin(utilbind.UTILITIES_DIRECTORY, name), f'{filename}.js')

@app.route('/u/<name>/<filename>.min.js')
def utilityMinifiedJavascriptAsset(name, filename):
    return send_from_directory(
        pjoin(utilbind.UTILITIES_DIRECTORY, name), f'{filename}.min.js')


if __name__ == '__main__':
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.run(port=PORT, use_reloader=True)
