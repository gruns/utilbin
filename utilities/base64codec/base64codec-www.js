// Copyright _!_
//
// License _!_
//
// Original author: Ansgar Grunseid

(function(root) {
  var encodeStr = Module.cwrap(
    'encodeStr', 'number', ['string', 'number', 'number']);
  var decodeStr = Module.cwrap(
    'decodeStr', 'number', ['string', 'number', 'number']);
  var wrapCodecAction = function(func) {
    return function(input) {
      var buf = Module._malloc(2 * input.length);
      var len = func(input, input.length, buf);
      var str = Pointer_stringify(buf, len);
      Module._free(buf);
      return str;
    };
  }

  root.base64codec = root.base64codec || {};
  root.base64codec.encode = wrapCodecAction(encodeStr);
  root.base64codec.decode = wrapCodecAction(decodeStr);
})(window);
