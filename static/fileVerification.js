// Details for specific file restriction types
const fileRestrictions = {
    "backgroundImage":  {
        "extensions": {
            "png": true,
            "jpg": true,
            "jpeg": true,
        },
        "maxSize": 5, // MB
        "totalLimit": 5
    },
    "gpxFile": {
        "extensions": {
            "gpx": true
        },
        "maxSize": 10,
        "totalLimit": 50
    }
}

// Given a file type, check fileRestrictions table to see if it is a valid file to upload
function fileUploadIsValid(fileType) {
    // Check that the file type has a valid restriction entry
    if (fileRestrictions[fileType] && fileRestrictions[fileType]["extensions"] && fileRestrictions[fileType]["maxSize"]) {
        const uploadBtn = document.getElementById(fileType);
        // Make sure the upload button for this input exists
        if (uploadBtn !== null) {
            const uploadedFiles = uploadBtn.files;
            var totalSize = 0;
            // Loop through all uploaded files
            for (var i = 0; i < uploadedFiles.length; ++i) {
                const file = uploadedFiles[i];
                const fileName = file.name.toLowerCase();
                const fileExtension = fileName.split(".").pop();

                // Make sure that the file has a valid file extension
                if (fileRestrictions[fileType]["extensions"][fileExtension] == true) {
                    const fileSize = file.size / 1000000; // MB
                    totalSize += fileSize;
                    // Make sure sum of file uploads is within size limit
                    if (totalSize >= fileRestrictions[fileType]["totalLimit"]) {
                        return {
                            "success": false,
                            "message": "Sum size of all uploaded files must be less than " + fileRestrictions[fileType]["totalLimit"].toString() + " MB."
                        }
                    }
                    // Make sure individual file is within size limit
                    else if (fileSize >= fileRestrictions[fileType]["maxSize"]) {
                        return {
                            "success": false,
                            "message": "Uploaded file must be smaller than " + fileRestrictions[fileType]["maxSize"].toString() + " MB."
                        };
                    }
                }
                // File has invalid extension
                else {
                    return {
                        "success": false,
                        "message": "Uploaded file can only be "  + Object.keys(fileRestrictions[fileType]["extensions"]).toString() + "."
                    };
                }
            }
        }
        // No upload button
        else {
            return {
                "success": false,
                "message": "Could not find upload button."
            };
        }
    }
    // No entry for this file type in fileRestrictions table
    else {
        return {
            "success": false,
            "message": "No matching file restriction configuration for type " + fileType + ".\n\nAllowed types are " + Object.keys(fileRestrictions).toString() + "."
        };
    }

    // Valid upload
    return {
        "success": true
    };
}

function verifyBackgroundImage() {
    const fileVerificationResult = fileUploadIsValid("backgroundImage");
    const uploadBtn = document.getElementById("backgroundImage");
    const blurIntensitySlider = document.getElementById("blurIntensityLabel");

    // Background image has been uploaded successfully, show the blur intensity slider
    if (fileVerificationResult["success"]) {
        if (blurIntensitySlider !== null) {
            blurIntensitySlider.parentNode.hidden = false;
        }
    }
    else {
        // Notify the player why the file was rejected
        alert(fileVerificationResult["message"]);

        if (uploadBtn !== null) {
            // Clear the image from the file input
            uploadBtn.value = null;
            // Hide the blur intensity slider, as the background image is invalid
            if (blurIntensitySlider !== null) {
                blurIntensitySlider.parentNode.hidden = true;
            }
        }
    }
    // Show/hide clear background button and flat background color inputs. They should never both be visible.
    document.getElementById("clearBackgroundButton").hidden = blurIntensitySlider.hidden;
    document.getElementById("backgroundColor").parentNode.hidden = !document.getElementById("clearBackgroundButton").hidden;
}

function verifyGPXFile() {
    const fileVerificationResult = fileUploadIsValid("gpxFile");
    const uploadBtn = document.getElementById("gpxFile");
    const gpxFiles = document.getElementById("gpxFile");
    const gpxFileSubmit = document.getElementById("GPXSubmit");

    // Invalid GPX file, notify user the reason and clear input
    if (!(fileVerificationResult["success"])) {
        alert(fileVerificationResult["message"]);

        if (uploadBtn !== null) {
            uploadBtn.value = null;
            gpxFileSubmit.hidden = true;
            gpxFileSubmit.disabled = true;
            // Mark upload GPX button as disabled
            $(gpxFileSubmit).addClass("disabled-button");
        }
    }
    else {
        // Valid GPX file uploaded, enable upload GPX button
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
        document.getElementById("blurIntensityLabel").parentNode.hidden = backgroundImage.value.length == 0;
        document.getElementById("clearBackgroundButton").hidden = backgroundImage.value.length == 0;
    }
    // Set initial disabled state of the GPX upload button
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
