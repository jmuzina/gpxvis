var prevWidth = 0;
var portrait;
var gpxUploadSection;

function refreshSize() {
    if (window.innerWidth < window.innerHeight && !portrait) {
        portrait = true;

        if (gpxUploadSection != null) {
            gpxUploadSection.hidden = true;
        }
    }
    else if (window.innerWidth >= window.innerHeight && portrait) {
        portrait = false;

        if (gpxUploadSection != null) {
            gpxUploadSection.hidden = false;
        }
    }
}

window.addEventListener("resize", refreshSize);
waitForElement("gpxUpload", function() {
    gpxUploadSection = document.getElementById("gpxUpload");
    if (gpxUploadSection != null) {
        portrait = (window.innerWidth < window.innerHeight);
        gpxUploadSection.hidden = portrait;
    }
});