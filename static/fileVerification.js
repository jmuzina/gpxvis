const imageFormats = {
    "png": true,
    "jpg": true,
    "jpeg": true,
    "gif": true
};

const maxImageSize = 50; // megabytes

function verifyBackgroundImage() {
    const uploadBtn = document.getElementById("backgroundImage");
    const uploadedFile = uploadBtn.value;
    const fileName = uploadedFile.toLowerCase();
    const fileExtension = fileName.split(".").pop();

    if (imageFormats[fileExtension] == true) {
        const fileSize = uploadBtn.files[0].size / 1000000; // megabytes
        return (fileSize < maxImageSize);
    }
    else {
        return false;
    }
}