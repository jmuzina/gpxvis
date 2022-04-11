const imageFormats = {
    "png": true,
    "jpg": true,
    "jpeg": true,
    "gif": true
};

const fileRestrictions = {
    "backgroundImage":  {
        "extensions": {
            "png": true,
            "jpg": true,
            "jpeg": true,
            "gif": true
        },
        "maxSize": 50, // MB
        "totalLimit": 50
    },
    "gpxFile": {
        "extensions": {
            "gpx": true
        },
        "maxSize": 10,
        "totalLimit": 50
    }
}

function fileUploadIsValid(fileType) {
    if (fileRestrictions[fileType] && fileRestrictions[fileType]["extensions"] && fileRestrictions[fileType]["maxSize"]) {
        const uploadBtn = document.getElementById(fileType);
        if (uploadBtn !== null) {
            const uploadedFiles = uploadBtn.files;
            var totalSize = 0;
            for (var i = 0; i < uploadedFiles.length; ++i) {
                const file = uploadedFiles[i];
                const fileName = file.name.toLowerCase();
                const fileExtension = fileName.split(".").pop();

                if (fileRestrictions[fileType]["extensions"][fileExtension] == true) {
                    const fileSize = file.size / 1000000; // MB
                    totalSize += fileSize;
                    if (totalSize >= fileRestrictions[fileType]["totalLimit"]) {
                        return {
                            "success": false,
                            "message": "Sum size of all uploaded files must be less than " + fileRestrictions[fileType]["totalLimit"].toString() + " MB."
                        }
                    }
                    else if (fileSize >= fileRestrictions[fileType]["maxSize"]) {
                        return {
                            "success": false,
                            "message": "Uploaded file must be smaller than " + fileRestrictions[fileType]["maxSize"].toString() + " MB."
                        };
                    }
                }
                else {
                    return {
                        "success": false,
                        "message": "Uploaded file can only be "  + Object.keys(fileRestrictions[fileType]["extensions"]).toString() + "."
                    };
                }
            }
        }
        else {
            return {
                "success": false,
                "message": "Could not find upload button."
            };
        }
    }
    else {
        return {
            "success": false,
            "message": "No matching file restriction configuration for type " + fileType + ".\n\nAllowed types are " + Object.keys(fileRestrictions).toString() + "."
        };
    }

    return {
        "success": true
    };
}


function verifyBackgroundImage() {
    const fileVerificationResult = fileUploadIsValid("backgroundImage");
    const uploadBtn = document.getElementById("backgroundImage");
    const blurIntensitySlider = document.getElementById("blurIntensityLabel");
    //const clearBackgroundButton =  document.getElementById("clearBackgroundButton");

    if (fileVerificationResult["success"]) {
        if (blurIntensitySlider !== null) {
            blurIntensitySlider.hidden = false;
        }
    }
    else {
        alert(fileVerificationResult["message"]);

        if (uploadBtn !== null) {
            uploadBtn.value = null;
            if (blurIntensitySlider !== null) {
                blurIntensitySlider.hidden = true;
            }
        }
    }
    document.getElementById("clearBackgroundButton").hidden = blurIntensitySlider.hidden;
    document.getElementById("backgroundColor").parentNode.hidden = !document.getElementById("clearBackgroundButton").hidden;
}

function verifyGPXFile() {
    const fileVerificationResult = fileUploadIsValid("gpxFile");
    const uploadBtn = document.getElementById("gpxFile");
    const gpxFiles = document.getElementById("gpxFile");
    const gpxFileSubmit = document.getElementById("GPXSubmit");

    if (!(fileVerificationResult["success"])) {
        alert(fileVerificationResult["message"]);

        if (uploadBtn !== null) {
            uploadBtn.value = null;
            gpxFileSubmit.hidden = true;
            gpxFileSubmit.disabled = true;
            $(gpxFileSubmit).addClass("disabled-button");
        }
    }
    else {
        if (gpxFiles !== null) {
            if (gpxFileSubmit !== null) {
                gpxFileSubmit.hidden = gpxFiles.value.length == 0;
                gpxFileSubmit.disabled = gpxFileSubmit.hidden;
                if (gpxFileSubmit.disabled) {
                    $(gpxFileSubmit).addClass("disabled-button");
                }
                else {
                    $(gpxFileSubmit).removeClass("disabled-button");
                }
            }
        }
    }
}

window.onload = function(){
    // Set background blur slider visibility depending on whether image is  cached 
    const backgroundImage =  document.getElementById("backgroundImage");
    const gpxFiles = document.getElementById("gpxFile");
    if (backgroundImage !== null) {
        document.getElementById("blurIntensityLabel").hidden = backgroundImage.value.length == 0;
        document.getElementById("clearBackgroundButton").hidden = backgroundImage.value.length == 0;
    }
    if (gpxFiles !== null) {
        const gpxFileSubmit = document.getElementById("GPXSubmit");
        if (gpxFileSubmit !== null) {
            gpxFileSubmit.hidden = gpxFiles.value.length == 0;
            gpxFileSubmit.disabled = gpxFileSubmit.hidden;
            if (gpxFileSubmit.disabled) {
                $(gpxFileSubmit).addClass("disabled-button");
            }
            else {
                $(gpxFileSubmit).removeClass("disabled-button");
            }
        }
    }
}
