// Wait for the existence of an HTML element, then call the supplied function
function waitForElement(elementID, callback) {
    if (document.getElementById(elementID)) callback();
    else {
      setTimeout(function () {
        waitForElement(elementID, callback);
      }, 50);
    }
  }