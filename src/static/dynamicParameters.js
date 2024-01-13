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
var silhouetteImage;
var duplicateActivities;
var overlayBackground;
var clearBackgroundButton;
var backgroundColor;

// Wait for all HTML elements to load, and assign them to variables
waitForElement("displayGridLines", function() { gridCheckBox = document.getElementById("displayGridLines"); });
waitForElement("gridlineColor", function() { gridlineColorSelector = document.getElementById("gridlineColor").parentNode; });
waitForElement("gridThickness", function() { gridThickness = document.getElementById("gridThickness"); gridlineThicknessSelector = gridThickness.parentNode; });
waitForElement("gridThicknessPreview", function() {gridThicknessPreview = document.getElementById("gridThicknessPreview"); });
waitForElement("pathThicknessPreview", function() { pathThicknessPreview = document.getElementById("pathThicknessPreview"); });
waitForElement("blurIntensityLabel", function() { blurIntensityLabel = document.getElementById("blurIntensityLabel"); });
waitForElement("blurIntensityPreview", function() { blurIntensityPreview = document.getElementById("blurIntensityPreview"); });
waitForElement("blurIntensity", function() { blurIntensity = document.getElementById("blurIntensity"); });
waitForElement("backgroundImage", function() { backgroundImage = document.getElementById("backgroundImage"); });
waitForElement("silhouetteImage", function() { silhouetteImage = document.getElementById("silhouetteImage").parentNode; });
waitForElement("duplicateActivities", function() { duplicateActivities = document.getElementById("duplicateActivities").parentNode; });
waitForElement("infoText", function() { overlayCheckBox = document.getElementById("infoText"); });
waitForElement("textBackgroundFade", function() { overlayBackground = document.getElementById("textBackgroundFade").parentNode; });
waitForElement("clearBackgroundButton", function() { clearBackgroundButton = document.getElementById("clearBackgroundButton"); });
waitForElement("backgroundColor", function() { backgroundColor = document.getElementById("backgroundColor").parentNode; });

// Show grid checkbox has been toggled
// Checked: show gridline thickness and color
// Unchecked: hide gridline thickness and color
function gridChecked() {
    gridlineColorSelector.parentNode.hidden = !gridCheckBox.checked;
    gridlineThicknessSelector.parentNode.hidden = 
    gridlineColorSelector.parentNode.hidden;
}

// Given a range input value, return its value as a % between min and max
function getSliderPercent(rangeElement) {
    return Math.ceil(((rangeElement.value / rangeElement.max) * 100)) + " %"
}

// Show overlay checkbox has been toggled
// Checked: Show overlay backdrop checkbox
// Unchecked: hide overlay backdrop checkbox
function overlayChecked() {
    overlayBackground.parentNode.hidden = !overlayCheckBox.checked;
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

// Silhoutte image value has changed
// Has a value: show the duplicate activities checkbox
// No value: hide the duplicate activities checkbox
function silhouetteImageSelected() {
    silhouetteImage = document.getElementById("silhouetteImage")
    if (silhouetteImage.value!=""){
        duplicateActivities.parentNode.hidden = false;
    }
    else{
        duplicateActivities.parentNode.hidden = true;
    }

}

// Clear the background image from the background image upload input
function clearBackground() {
    backgroundImage.value = null;
    clearBackgroundButton.hidden = true;
    blurIntensityLabel.parentNode.hidden = true;
    backgroundColor.hidden = false;
}

// Perform page-load setup
setTimeout(function () {
    // Set initial visibility of dependent form inpjuts
    overlayChecked();
    gridThicknessChanged();
    blurIntensityChanged();
    silhouetteImageSelected();
    gridlineThicknessSelector.parentNode.hidden = !gridCheckBox.checked;
    blurIntensityLabel.parentNode.hidden = backgroundImage.value.length == 0;
    clearBackgroundButton.hidden = blurIntensityLabel.parentNode.hidden;
    backgroundColor.hidden = !clearBackgroundButton.hidden;
    

    // Listen for value changes and adjust accordingly
    overlayCheckBox.addEventListener("change", overlayChecked, false);
    pathThickness.addEventListener("input", pathThicknessChanged, false);
    gridThickness.addEventListener("input", gridThicknessChanged, false);
    gridCheckBox.addEventListener("change", gridChecked, false);
    blurIntensity.addEventListener("input", blurIntensityChanged, false);
    silhouetteImage.addEventListener("change", silhouetteImageSelected, false);
    clearBackgroundButton.addEventListener("click", clearBackground, false);

    gridThicknessChanged();
    pathThicknessChanged();
    blurIntensityChanged();
}, 500);