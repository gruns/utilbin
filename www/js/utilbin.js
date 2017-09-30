// Copyright _!_
//
// License _!_
//
// Original author: Ansgar Grunseid

var utilbin = window.utilbin || {};
(function() {

  // Workaround to call functions with keyword arguments for the dogshit
  // language that is Javascript. See https://stackoverflow.com/a/11796776.
  var wrapWithKeywordArguments = (function() {
    var pattern = /function[^(]*\(([^)]*)\)/;

    return function(func) {
      // fails horribly for parameterless functions ;)
      var args = func.toString().match(pattern)[1].split(/,\s*/);

      return function() {
        var named_params = arguments[arguments.length - 1];
        if (typeof named_params === 'object') {
          var params = [].slice.call(arguments, 0, -1);
          if (params.length < args.length) {
            for (var i = params.length, l = args.length; i < l; i++) {
              params.push(named_params[args[i]]);
            }
            return func.apply(this, params);
          }
        }
        return func.apply(null, arguments);
      };
    };
  }());


  // The function below is loosely based on the code here:
  // https://code.google.com/archive/p/form-serialize/.
  function serializeFormFieldsToActionAndArgs(form) {
    var argobj = {};
    var action = null;

    for (let ele of form.elements) {
      var tagName = ele.tagName.toLowerCase();
      if (ele.disabled) {
        continue;
      } else if (tagName === 'input') {
        var includeAsValue = [
          'text', 'hidden', 'password', 'button', 'reset', 'number'];
        if (includeAsValue.indexOf(ele.type) > -1)
          argobj[ele.name] = ele.value;
        else if (['radio', 'checkbox'].indexOf(ele.type) > -1)
          argobj[ele.name] = ele.checked ? ele.value : false;
        else if (ele.type === 'submit')
          argobj[ele.name] = ele.value;
      } else if (tagName === 'textarea') {
        argobj[ele.name] = ele.value;
      } else if (tagName === 'select') {
        if (ele.type == 'select-one') {
          argobj[ele.name] = ele.value;
        } else if (ele.type == 'select-multiple') {
          var values = [];
          for (let option of ele.options)
            values.push(option.selected ? option.value : false)
          argobj[ele.name] = values;
        }              
      } else if (tagName === 'button' && ele.hasAttribute('selected')) {
        action = ele.value;
      }
    }

    return {'action': action, 'argobj': argobj};
  }


  function runUtility(name, action, argobj) {
    var wrapped = wrapWithKeywordArguments(window[name][action]);
    output = wrapped(argobj);
    return output;
  }

  utilbin.selectActionButton = function(button) {
    for (let ele of button.parentNode.getElementsByTagName('button'))
      ele.removeAttribute('selected');
    button.setAttribute('selected', "");
  }

  utilbin.onInputChange = function(ele) {
    var form = ele.parentNode;
    var utilName = window.location.pathname.split('/u/')[1];

    var o = serializeFormFieldsToActionAndArgs(form);
    var output = runUtility(utilName, o.action, o.argobj);

    // TODO(grun): Syntax highlight the output, like with
    // https://highlightjs.org/.
    document.getElementById('output').value = output;
  }

})();

document.addEventListener('DOMContentLoaded', function() {
  // pass
});
