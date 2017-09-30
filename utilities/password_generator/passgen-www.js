// Copyright _!_
//
// License _!_
//
// Original author: Ansgar Grunseid

(function(root) {
  var generatePassword = require('./password-generator.js');

  root.password_generator = root.password_generator || {};
  root.password_generator.generate = function(length) {
    return generatePassword(length);
  }
})(window);
