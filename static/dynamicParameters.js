var gridCheckBox;
var gridlineColorSelector;
var gridThickness;
var gridlineThicknessSelector;
var gridThicknessPreview;
var pathThicknessPreview;
var blurIntensityLabel;
var blurIntensityPreview;
var blurIntensity;
var backgroundImage;
var overlayCheckBox;
var overlayBackground;
var clearBackgroundButton;
var backgroundColor;

waitForElement("displayGridLines", function() { gridCheckBox = document.getElementById("displayGridLines"); });
waitForElement("gridlineColor", function() { gridlineColorSelector = document.getElementById("gridlineColor").parentNode; });
waitForElement("gridThickness", function() { gridThickness = document.getElementById("gridThickness"); gridlineThicknessSelector = gridThickness.parentNode; });
waitForElement("gridThicknessPreview", function() {gridThicknessPreview = document.getElementById("gridThicknessPreview"); });
waitForElement("pathThicknessPreview", function() { pathThicknessPreview = document.getElementById("pathThicknessPreview"); });
waitForElement("blurIntensityLabel", function() { blurIntensityLabel = document.getElementById("blurIntensityLabel"); });
waitForElement("blurIntensityPreview", function() { blurIntensityPreview = document.getElementById("blurIntensityPreview"); });
waitForElement("blurIntensity", function() { blurIntensity = document.getElementById("blurIntensity"); });
waitForElement("backgroundImage", function() { backgroundImage = document.getElementById("backgroundImage"); });
waitForElement("infoText", function() { overlayCheckBox = document.getElementById("infoText"); });
waitForElement("textBackgroundFade", function() { overlayBackground = document.getElementById("textBackgroundFade").parentNode; });
waitForElement("clearBackgroundButton", function() { clearBackgroundButton = document.getElementById("clearBackgroundButton"); });
waitForElement("backgroundColor", function() { backgroundColor = document.getElementById("backgroundColor").parentNode; });

function gridChecked() {
    gridlineColorSelector.hidden = !gridCheckBox.checked;
    gridlineThicknessSelector.hidden =
    gridlineColorSelector.hidden;
}

function getSliderPercent(rangeElement) {
    return Math.ceil(((rangeElement.value / rangeElement.max) * 100)) + " %"
}

function overlayChecked() {
    overlayBackground.hidden = !overlayCheckBox.checked;
}

function gridThicknessChanged() {
    gridThicknessPreview.innerHTML = getSliderPercent(gridThickness);
    
}

function pathThicknessChanged() {
    pathThicknessPreview.innerHTML = getSliderPercent(pathThickness);
}

function blurIntensityChanged() {
    blurIntensityPreview.innerHTML = getSliderPercent(blurIntensity);
}

function clearBackground() {
    backgroundImage.value = null;
    clearBackgroundButton.hidden = true;
    blurIntensityLabel.hidden = true;
    backgroundColor.hidden = false;
}

setTimeout(function () {
    // Bootstrap
    overlayChecked();
    gridThicknessChanged();
    blurIntensityChanged();
    gridlineThicknessSelector.hidden = !gridCheckBox.checked;
    blurIntensityLabel.hidden = backgroundImage.value.length == 0;
    clearBackgroundButton.hidden = blurIntensityLabel.hidden;
    backgroundColor.hidden = !clearBackgroundButton.hidden;


    // Listen for value changes and adjust accordingly
    overlayCheckBox.addEventListener("change", overlayChecked, false);
    pathThickness.addEventListener("input", pathThicknessChanged, false);
    gridThickness.addEventListener("input", gridThicknessChanged, false);
    gridCheckBox.addEventListener("change", gridChecked, false);
    blurIntensity.addEventListener("input", blurIntensityChanged, false);
    clearBackgroundButton.addEventListener("click", clearBackground, false);
}, 500);