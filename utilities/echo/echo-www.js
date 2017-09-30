// Copyright _!_
//
// License _!_
//
// Original author: Ansgar Grunseid

(function(root) {
  var mirror = Module.cwrap('mirror', 'number', ['string', 'number']);
  var wrapAction = function(func) {
    return function(input) {
      var buf = Module._malloc(input.length + 1);
      var len = func(input, buf);
      var str = Pointer_stringify(buf, len);
      Module._free(buf);
      return str;
    };
  }

  root.echo = root.echo || {};
  root.echo.mirror = wrapAction(mirror, 2);
})(window);
