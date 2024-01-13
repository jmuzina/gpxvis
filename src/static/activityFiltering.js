var selectedIDs = [];

// Allows jinja2 template values from flask to be read into JavaScript
// credit https://stackoverflow.com/questions/37259740/passing-variables-from-flask-to-javascript
function pythonBridge(vars) {
  return vars
}

// Returns all activities that contain the provided string in their name
function getKeywordMatches(arr, inputStr) {
  inputStr = inputStr.toLowerCase();
  return arr.filter(([key, value]) => value["name"].toLowerCase().includes(inputStr))
}

function configureDateFields(startDate, endDate) {
  var startDateField = document.getElementById("start-date");
  var endDateField = document.getElementById("end-date");

  // Set date field values and maximums
  startDateField.setAttribute("value", startDate);
  startDateField.setAttribute("max", endDate);

  endDateField.setAttribute("value", endDate);
  endDateField.setAttribute("max", endDate);
}

// Returns all activities that were recorded between the specified start and end dates
// credit https://stackoverflow.com/questions/2488313/javascripts-getdate-returns-wrong-date
function getDateMatches(startDate, endDate) {
  const splitStartDate = startDate.match(/(\d+)/g);
  if (splitStartDate == null) return [];
  const filterStartDate = new Date(splitStartDate[0], splitStartDate[1] - 1, splitStartDate[2]);

  const splitEndDate = endDate.match(/(\d+)/g);
  if (splitEndDate == null) return [];
  const filterEndDate = new Date(splitEndDate[0], splitEndDate[1] - 1, splitEndDate[2]);

  return activitiesAsArray.filter(([key, value]) => {
    const splitActivityDate = value["displayTime"].match(/(\d+)/g);
    const filterActivityDate = new Date(splitActivityDate[2], splitActivityDate[0] - 1, splitActivityDate[1])
    return filterActivityDate >= filterStartDate && filterActivityDate <= filterEndDate;
  });
}

// Returns all activities that match the provided activity type
function getActivityTypeMatches(activityType) {
  activityType = activityType.toLowerCase();

  // If activity type is all, we should return all activities
  if (activityType == "all") {
    return activitiesAsArray;
  }
  else {
    return activitiesAsArray.filter(([key, value]) => value["type"].toLowerCase() == activityType);
  }
}

// Returns all activities that match all three filters
// Gets the intersection of the three filter results and returns it
// credit https://stackoverflow.com/questions/1885557/simplest-code-for-array-intersection-in-javascript
function getFilterMatches(arr) {
  var startDateField = document.getElementById("start-date");
  var endDateField = document.getElementById("end-date");
  var activityTypeField = document.getElementById("activity-type");
  var keywordField = document.getElementById("keyword")

  const keywordMatches = getKeywordMatches(arr, keywordField["value"]);
  const dateMatches = getDateMatches(startDateField["value"], endDateField["value"]);
  const activityTypeMatches = getActivityTypeMatches(activityTypeField["value"]);

  // Intersection of keyword and date matches
  const keywordDateMatches = keywordMatches.filter((dateMatch) => {
    return dateMatches.indexOf(dateMatch) !== -1;
  });
  // Intersection of keyword-date matches and activity type matches
  return keywordDateMatches.filter((keywordDateMatch) => {
    return activityTypeMatches.indexOf(keywordDateMatch) !== -1;
  });
}

// Find all activities that match the provided inputs and displays them on-screen.
// Called every time "get activities" is clicked.
function searchActivities(activities) {
  const filterMatches = getFilterMatches(activities);

  const oldTableBody = document.getElementById("matchedActivities");
  var table = document.getElementById("activitiesTable");
  const tableHeader = document.getElementById("activitiesTableHeader");

  selectedIDs = [];
  selectedActivitiesDistance = 0
  selectedActivitiesLength = 0

  if (filterMatches.length > 0) {
    var newTableBody = document.createElement('tbody');
    newTableBody.id = "matchedActivities";
    // credit https://codedec.com/tutorials/how-to-add-new-row-in-table-using-javascript/
    for (var i = 0; i < filterMatches.length; ++i) {
      const activity = filterMatches[i][1];
      for (var j = 0; j < 1; ++j) {
        var row = newTableBody.insertRow(i + j);
        var nameCell = row.insertCell(0);
        var dateCell = row.insertCell(1);
        var typeCell = row.insertCell(2);
        var distanceCell = row.insertCell(3);

        nameCell.innerHTML = activity["name"];
        nameCell.className = "nameCell";
        dateCell.innerHTML = activity["displayTime"];
        dateCell.className = "dateCell";
        typeCell.innerHTML = activity["type"];
        typeCell.className = "typeCell";
        distanceCell.innerHTML = activity["distance"] + " mi";
        distanceCell.className = "distanceCell";
        selectedActivitiesDistance += activity["distance"];
        selectedActivitiesLength += activity["duration"];
      }
      selectedIDs[i] = filterMatches[i][0];
    }

    oldTableBody.parentNode.replaceChild(newTableBody, oldTableBody);
    tableHeader.hidden = false;
    table.hidden = false;
    var generateButton = document.getElementById("generate-button");
    generateButton.disabled = false;
    $("#generate-button").removeClass("disabled-button");
  }
  else {
    tableHeader.hidden = true;
    table.hidden = true;
    table.style = "";
    var generateButton = document.getElementById("generate-button");
    generateButton.disabled = true;
    $("#generate-button").addClass("disabled-button");
  }

  const selectedActivitiesElement = document.getElementById("selectedActivities");
  selectedActivitiesElement["value"] = selectedIDs;
  selectedActivitiesElement.setAttribute("value", selectedIDs);
  const selectedLengthElement = document.getElementById("selectedActivityLength");
  const selectedDistanceElement = document.getElementById("selectedActivityDistance");
  selectedLengthElement["value"] = selectedActivitiesLength;
  selectedLengthElement.setAttribute("value", selectedActivitiesLength);
  selectedDistanceElement["value"] = Math.round(selectedActivitiesDistance);
  selectedDistanceElement.setAttribute("value", Math.round(selectedActivitiesDistance));
}

// Element IDs of parameter input elements that should cause a live update of
// the selected activities table on element change
const filterFieldIDs = [
  "start-date",
  "end-date",
  "activity-type",
  "keyword"
];

setTimeout(function() {
	// GPX Upload, not API pull: enable generate button and change active tab to background tab (activities tab is hidden)
	if (document.getElementById("v-pills-activities-tab") == null) {
  		waitForElement("generate-button", function() {
    		const generateButton = document.getElementById("generate-button");
    		generateButton.disabled = false;
    		$(generateButton).removeClass("disabled-button");
    		$("#v-pills-background-tab").addClass("active");
    		$("#v-pills-background").addClass("show");
    		$("#v-pills-background").addClass("active");
  		});
	}
}, 500);
