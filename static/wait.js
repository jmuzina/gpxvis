function waitForElement(elementID, callback) {
    if (document.getElementById(elementID)) callback();
    else {
      setTimeout(function () {
        waitForElement(elementID, callback);
      }, 50);
    }
  }