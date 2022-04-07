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
        "maxSize": 50 // MB
    },
    "uploadedActivity": {
        "extensions": {
            "gpx": true
        },
        "maxSize": 50
    }
}

function fileUploadIsValid(fileType) {
    if (fileRestrictions[fileType] && fileRestrictions[fileType]["extensions"] && fileRestrictions[fileType]["maxSize"]) {
        const uploadBtn = document.getElementById(fileType);
        if (uploadBtn !== null) {
            const uploadedFile = uploadBtn.value;
            const fileName = uploadedFile.toLowerCase();
            const fileExtension = fileName.split(".").pop();

            if (fileRestrictions[fileType]["extensions"][fileExtension] == true) {
                const fileSize = uploadBtn.files[0].size / 1000000; // MB
                if (fileSize < fileRestrictions[fileType]["maxSize"]) {
                    return {
                        "success": true,
                        "message": ""
                    };
                }
                else {
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
}


function verifyBackgroundImage(fileType = "") {
    const fileVerificationResult = fileUploadIsValid(fileType);
    const uploadBtn = document.getElementById(fileType);
    const blurIntensitySlider = document.getElementById("blurIntensityLabel");

    if (fileVerificationResult["success"]) {
        if (fileType  == "backgroundImage") {
            if (blurIntensitySlider !== null) {
                blurIntensitySlider.hidden = false;
            }
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
}

window.onload = function(){
    // Set background blur slider visibility depending on whether image is  cached 
    const backgroundImage =  document.getElementById("backgroundImage").value;
    document.getElementById("blurIntensityLabel").hidden = backgroundImage.length == 0;
}
