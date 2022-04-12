var prevWidth = 0;
var portrait;

function refreshSize() {
    const gpxUploadSection = document.getElementById("gpxUpload");

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
window.onload = function() {
    console.log('loaded');
    const gpxUploadSection = document.getElementById("gpxUpload");
    console.log(window.innerWidth);
    if (gpxUploadSection != null) {
        console.log("setting hidden state");
        portrait = (window.innerWidth < window.innerHeight);
        gpxUploadSection.hidden = portrait;
    }
}