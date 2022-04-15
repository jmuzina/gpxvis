var prevWidth = 0;
var portrait;
var gpxUploadSection;

// Window size has been changed
function refreshSize() {
    // Window size changing to portrait, hide GPX upload section
    if (window.innerWidth < window.innerHeight && !portrait) {
        portrait = true;

        if (gpxUploadSection != null) {
            gpxUploadSection.hidden = true;
        }
    }
    // Window size changing to desktop, show GPX upload section
    else if (window.innerWidth >= window.innerHeight && portrait) {
        portrait = false;

        if (gpxUploadSection != null) {
            gpxUploadSection.hidden = false;
        }
    }
}

window.addEventListener("resize", refreshSize); // listen for resize events

// Set initial hidden state of GPX upload section
waitForElement("gpxUpload", function() {
    gpxUploadSection = document.getElementById("gpxUpload");
    if (gpxUploadSection != null) {
        portrait = (window.innerWidth < window.innerHeight);
        gpxUploadSection.hidden = portrait;
    }
});
