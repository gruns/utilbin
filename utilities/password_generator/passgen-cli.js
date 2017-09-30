#!/usr/bin/env node

// Copyright _!_
//
// License _!_
//
// Original author: Ansgar Grunseid

var path = require('path');
var minimist = require(
  path.resolve(__dirname, './minimist.js'));
var generatePassword = require(
  path.resolve(__dirname, './password-generator.js'));

var args = minimist(process.argv);
var password = generatePassword(args.l || args.length);

console.log(password);
