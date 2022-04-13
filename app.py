# App launch-point

# ---- Dependency imports ---- #
from enum import unique
import logging
import math
import os
import time
from configparser import ConfigParser, RawConfigParser
from datetime import datetime, timedelta
from os.path import exists
from werkzeug.utils import secure_filename

from flask import (Flask, Response, redirect, render_template, request,
                   send_file, session, url_for)
from flask_assets import Bundle, Environment

import functions
import generateVis
import SessionTimer
import glob
import shutil

# ---------------------------- #
ALLOWED_EXTENSIONS = {'png', 'jpeg', 'jpg', 'gpx'}
#IS_SERVER = exists("/etc/letsencrypt/live/capstone3.cs.kent.edu/fullchain.pem") and exists("/etc/letsencrypt/live/capstone3.cs.kent.edu/privkey.pem")

flaskApp = Flask(__name__)
flaskApp.config['TEMPLATES_AUTO_RELOAD'] = True
flaskApp.config['UPLOAD_FOLDER'] = "uploads"
# Hex-encoded random 24 character string for session encryption
flaskApp.secret_key = os.urandom(32)

if not os.path.exists("logs"):
    os.makedirs("logs")
if not os.path.exists("logs/flask"):
    os.makedirs("logs/flask")
if not os.path.exists("logs/console"):
    os.makedirs("logs/console")

# Clear all files in uploads directory on app launch
# https://www.tutorialspoint.com/How-to-delete-all-files-in-a-directory-with-Python
for root, dirs, files in os.walk("uploads"):
    for file in files:
        os.remove(os.path.join(root, file))

for sub_folder in glob.glob("uploads"):
    shutil.rmtree(sub_folder)

if not os.path.exists("uploads"):
    os.makedirs("uploads")

logFileName = str(datetime.utcnow()).replace(" ", "").replace(":", "").replace(".", "") + ".log"

flaskLogFile = logging.FileHandler("logs/flask/" + logFileName)
werkzeugLogger = logging.getLogger('werkzeug')
werkzeugLogger.addHandler(flaskLogFile)

consoleLogFile = logging.FileHandler("logs/console/" + logFileName)
flaskApp.logger.addHandler(consoleLogFile)
flaskApp.logger.setLevel(logging.DEBUG)

# ---- Bundle all scss files into all.css ---- #
assets     = Environment(flaskApp)
assets.url = flaskApp.static_url_path
scss       = Bundle('style.scss', filters='pyscss', output='all.css')
assets.config['SECRET_KEY'] = os.urandom(32)
assets.config['PYSCSS_LOAD_PATHS'] = assets.load_path
assets.config['PYSCSS_STATIC_URL'] = assets.url
assets.config['PYSCSS_STATIC_ROOT'] = assets.directory
assets.config['PYSCSS_ASSETS_URL'] = assets.url
assets.config['PYSCSS_ASSETS_ROOT'] = assets.directory

assets.register('scss_all', scss)
# -------- Read and load config data -------- #
configParser = RawConfigParser()   
configFilePath = r'./app.cfg'
configParser.read(configFilePath)

config = ConfigParser()
config.read_file(open(r'./app.cfg'))
# -------------------------------------------- #

import networks.strava  # Must be imported after config has been read
import networks.twitter

userCachedData = {}

apis = {
    'strava': networks.strava.StravaApi(config, flaskApp),
    'twitter': networks.twitter.twitterApi(config, flaskApp)
}

shareAuthURLs = {}

for networkName in apis:
    if not apis[networkName].loginWith:
        shareAuthURLs[networkName] = apis[networkName].authUrl

# Index page
@flaskApp.route('/')
def render_index():
    # Render homepage with userdata if it exists
    sessionDataValidationResult = functions.validUserData(session)

    if sessionDataValidationResult == True: # User already logged in, redirect to parameters page
	    return redirect(url_for("render_parameters"))
    elif sessionDataValidationResult == False or ("networkName" in session and session["networkName"] == "gpxFile"): # No user ID, not logged in.
        networks = {}
        for networkName in apis:
            if apis[networkName].loginWith:
                networkDetails = False
                if apis[networkName].isAvailable():
                    networkDetails = apis[networkName].authUrl
                
                networks[networkName] = networkDetails

        return render_template("index.html", networks = networks)
    else:
        return sessionDataValidationResult

@flaskApp.route('/logout')
def logout():
    # Clear user session data
    functions.wipeSession(session)

    # Wipe user cached data
    if "userData" in session and "id" in session["userData"] and "networkName" in session:
        uniqueId = functions.uniqueUserId(session["networkName"], session["userData"]["id"])
        #userImages[uniqueId] = None
        userCachedData[uniqueId] = None

    return redirect(url_for('render_index'))

@flaskApp.route('/parameters', methods=["POST", "GET"])
def render_parameters():
    refreshSessionTimer()
    sessionDataValidationResult = functions.validUserData(session)

    if request.method == "POST" and "gpxFile" in request.files:
        if not "userData" in session:
            id = None
            session["networkName"] = "gpxFile"

            # Get random ID for gpx file uploader and ensure nobody else has the same ID
            while ((id == None) or (functions.uniqueUserId(session["networkName"], id) in userCachedData)):
                id = functions.randomAlphanumericString(16)

            session["userData"] = {
                "id": id
            }

        uniqueId = functions.uniqueUserId(session["networkName"], session["userData"]["id"])

        if not os.path.exists("uploads/" + uniqueId):
            os.makedirs("uploads/" + uniqueId)

        for file in request.files.getlist('gpxFile'):
            if file and functions.allowed_file(file.filename, ALLOWED_EXTENSIONS):
                filename = secure_filename(functions.randomAlphanumericString(16) + "_" + file.filename)
                #print(file)
                file.save(os.path.join(flaskApp.config['UPLOAD_FOLDER'] + "/" + uniqueId, filename))     

        if not uniqueId in userCachedData:
            userCachedData[uniqueId] = {}

        return render_template("parameters.html", isGuest = True)

    elif sessionDataValidationResult == True:
        uniqueId = functions.uniqueUserId(session["networkName"], session["userData"]["id"])
        if len(userCachedData[uniqueId]["activities"]) > 0:
            currentDate = datetime.now()
            currentDateStr = datetime.strftime(currentDate, "%Y-%m-%d")
            yearAgoTime = currentDate- timedelta(days = 365)
            yearAgoStr = datetime.strftime(yearAgoTime, "%Y-%m-%d")
            return render_template("parameters.html", userData = session['userData'], activities = userCachedData[uniqueId]["activities"], startDate = yearAgoStr, endDate = currentDateStr)
        else:
            return functions.throwError("No activities found in your account.")
    elif sessionDataValidationResult == False: # No userdata, render guest homepage
        return redirect(url_for("render_index"))
    else: # error thrown
        return sessionDataValidationResult

@flaskApp.route('/errorPage')
def render_errorPage():
    refreshSessionTimer()

    errorMessage = request.args.get("errorMsg")
    if errorMessage == None:
        errorMessage = "Unknown Error"

    if "userData" in session:
        return render_template("errorPage.html", userData = session['userData'], errorMessage = errorMessage)
    else:
        return render_template("errorPage.html", errorMessage = errorMessage)

@flaskApp.route('/generatePage', methods = ["POST", "GET"])
def render_generatePage():
    refreshSessionTimer()

    twitterUsername = request.args.get("twitterUsername")
    tweetID = request.args.get("tweetID")

    uniqueId = None

    if "userData" in session:
        if "id" in session["userData"]:
            if "networkName" in session:
                uniqueId = functions.uniqueUserId(session["networkName"], session["userData"]["id"])

    if uniqueId == None:
        return redirect(url_for("render_index"))
    elif not (twitterUsername and tweetID): # process generate form inputs
        # default values of form arguments
        formArgs = {
            "backgroundColor": (255,255,255),
            "backgroundImage": "",
            "blurIntensity": 5,
            "pathThickness": 5,
            "pathColor": (0,0,0),
            "displayGridLines": False,
            "silhouetteImage": "",
            "duplicateActivities": False,
            "gridThickness": 5,
            "gridlineColor": (0,0,0),
            "beforeTime": str(math.floor(time.time())),
            "afterTime": str(0),
            "selectedActivities": "",
            "infoText": False,
            "textBackgroundFade": False
        }

        # Set form args to received form submission
        for key in formArgs:
            if key in request.form:
                formArgs[key] = request.form[key]
        
        selected = None
        if (session["networkName"] != "gpxFile"):
            selected = dict([(activityID, userCachedData[uniqueId]["activities"][activityID]) for activityID in userCachedData[uniqueId]["activities"] if str(activityID) in formArgs["selectedActivities"]])
        
        if session["networkName"] == "gpxFile" or len(selected) > 0:
            data = None
            if session["networkName"] != "gpxFile":
                data = apis[session["networkName"]].getAllPolylines(selected)
            else:
                data = uniqueId
            
            filename = ""
            # Pass a background image into the visualizer if one was given
            if "backgroundImage" in request.files:
                file = request.files['backgroundImage']

                if file and functions.allowed_file(file.filename, ALLOWED_EXTENSIONS):
                    filename = secure_filename(file.filename)
                    file.save(os.path.join(flaskApp.config['UPLOAD_FOLDER'], filename))

            totalLength = request.form["selectedActivityLength"]
            totalDistance = request.form["selectedActivityDistance"]

            if session["networkName"] != "gpxFile":
                userCachedData[uniqueId]["visualizationResult"] = functions.getImageBase64String(generateVis.getVis(data=data, lineThickness=int(formArgs["pathThickness"]), gridOn=formArgs["displayGridLines"] == "on", backgroundColor=formArgs["backgroundColor"], backgroundImage = filename, backgroundBlur = formArgs["blurIntensity"], foregroundColor=formArgs["pathColor"], gridColor=formArgs["gridlineColor"], gridThickness=int(formArgs["gridThickness"]), infoText=formArgs["infoText"],silhouetteImage=formArgs["silhouetteImage"], duplicateActivities=formArgs["duplicateActivities"], textBackgroundFade=formArgs["textBackgroundFade"], totalTime=functions.getTimeStr(totalLength), totalDistance=str(totalDistance) + " mi."))
            else:
                userCachedData[uniqueId]["visualizationResult"] = functions.getImageBase64String(generateVis.getVis(data=data, lineThickness=int(formArgs["pathThickness"]), gridOn=formArgs["displayGridLines"] == "on", backgroundColor=formArgs["backgroundColor"], backgroundImage = filename, backgroundBlur = formArgs["blurIntensity"], foregroundColor=formArgs["pathColor"], gridColor=formArgs["gridlineColor"], gridThickness=int(formArgs["gridThickness"]), infoText=formArgs["infoText"], silhouetteImage=formArgs["silhouetteImage"], duplicateActivities=formArgs["duplicateActivities"], textBackgroundFade=formArgs["textBackgroundFade"]))

            return render_template("generatePage.html", userData = session['userData'], shareAuthURLs = shareAuthURLs, visualization =  userCachedData[uniqueId]["visualizationResult"])
        else:
            return functions.throwError("No activities were selected.")

    elif uniqueId in userCachedData and "visualizationResult" in userCachedData[uniqueId]: # User has just shared the post to social media
        return render_template("generatePage.html", userData = session['userData'], shareAuthURLs = shareAuthURLs, visualization =  userCachedData[uniqueId]["visualizationResult"], tweetLink = "https://twitter.com/" + twitterUsername + "/status/" + tweetID)
    else:
        return functions.throwError("Social media share results were given but no visualization was found.")

# Update user activity tracker
def refreshSessionTimer():
    sessionDataValidationResult = functions.validUserData(session)
    if sessionDataValidationResult == True:
        uniqueId = functions.uniqueUserId(session["networkName"], session["userData"]["id"])
        # Valid activity tracker exists: Check whether it is expired
        if "sessionTimer" in userCachedData[uniqueId]:
            # User's session has not expired: restart the timer
            if not userCachedData[uniqueId]["sessionTimer"].expired():
                userCachedData[uniqueId]["sessionTimer"].start()
            # User has been inactive too long: wipe their session data
            else:
                functions.wipeSession(session)
        # User has no session timer: start one
        else:
            userCachedData[uniqueId]["sessionTimer"] = SessionTimer.SessionTimer()

@flaskApp.route("/activityFiltering.js")
def returnActivityFiltering():
    return send_file("./static/activityFiltering.js")

@flaskApp.route("/fileVerification.js")
def returnFileVerification():
    return send_file("./static/fileVerification.js")

@flaskApp.route("/dynamicParameters.js")
def returnDynamicParameters():
    return send_file("./static/dynamicParameters.js")

@flaskApp.route("/resize.js")
def returnResize():
    return send_file("./static/resize.js")

@flaskApp.route("/wait.js")
def returnWait():
    return send_file("./static/wait.js")

@flaskApp.route('/aboutPage')
def render_aboutPage():
    refreshSessionTimer()
    sessionDataValidationResult = functions.validUserData(session)

    if sessionDataValidationResult == True:
        return render_template('aboutPage.html', userData = session['userData'])
    else:
        return render_template('aboutPage.html')

@flaskApp.route('/privacyPage')
def render_privacyPage():
    refreshSessionTimer()
    sessionDataValidationResult = functions.validUserData(session)

    if sessionDataValidationResult == True:
        return render_template('privacyPage.html', userData = session['userData'])
    else:
        return render_template('privacyPage.html')

# Store any config items not related to API logins under app.config
for key in config["DEFAULT"]:
    flaskApp.config[key] = config["DEFAULT"][key]

#print(networks.twitter.twitterApi(config, flaskApp).getAccessKey())