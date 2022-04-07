window.onload = function() {
    var gridCheckBox = document.getElementById("displayGridLines");
    var gridlineColorSelector = document.getElementById("gridlineColor").parentNode;
    var gridThickness = document.getElementById("gridThickness");
    var gridlineThicknessSelector = gridThickness.parentNode;
    var gridThicknessPreview = document.getElementById("gridThicknessPreview");
    var pathThicknessPreview = document.getElementById("pathThicknessPreview");
    const blurIntensityLabel = document.getElementById("blurIntensityLabel");
    const blurIntensityPreview = document.getElementById("blurIntensityPreview");
    const blurIntensity = document.getElementById("blurIntensity");
    const backgroundImage =  document.getElementById("backgroundImage");
    var overlayCheckBox = document.getElementById("infoText");
    var overlayBackground = document.getElementById("textBackgroundFade").parentNode;
    const clearBackgroundButton = document.getElementById("clearBackgroundButton");

    function gridChecked() {
        gridlineColorSelector.hidden = !gridCheckBox.checked;
        gridlineThicknessSelector.hidden =
        gridlineColorSelector.hidden;
    }

    function overlayChecked() {
        overlayBackground.hidden = !overlayCheckBox.checked;
    }

    function gridThicknessChanged() {
        gridThicknessPreview.innerHTML = gridThickness.value;
    }

    function pathThicknessChanged() {
        pathThicknessPreview.innerHTML = pathThickness.value;
    }

    function blurIntensityChanged() {
        blurIntensityPreview.innerHTML = blurIntensity.value;
    }

    function clearBackground() {
        backgroundImage.value = null;
        clearBackgroundButton.hidden = true;
        blurIntensityLabel.hidden = true;
    }

    // Bootstrap
    overlayChecked();
    gridThicknessChanged();
    blurIntensityChanged();
    gridlineThicknessSelector.hidden = !gridCheckBox.checked;
    blurIntensityLabel.hidden = backgroundImage.value.length == 0;
    clearBackgroundButton.hidden = blurIntensityLabel.hidden;


    // Listen for value changes and adjust accordingly
    overlayCheckBox.addEventListener("change", overlayChecked, false);
    pathThickness.addEventListener("change", pathThicknessChanged, false);
    gridThickness.addEventListener("change", gridThicknessChanged, false);
    gridCheckBox.addEventListener("change", gridChecked, false);
    blurIntensity.addEventListener("change", blurIntensityChanged, false);
    clearBackgroundButton.addEventListener("click", clearBackground, false);
}