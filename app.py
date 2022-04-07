# App launch-point

# ---- Dependency imports ---- #
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

# ---------------------------- #
ALLOWED_EXTENSIONS = {'png', 'jpeg', 'jpg', 'gif', 'gpx'}
IS_SERVER = exists("/etc/letsencrypt/live/capstone3.cs.kent.edu/fullchain.pem") and exists("/etc/letsencrypt/live/capstone3.cs.kent.edu/privkey.pem")

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
if not os.path.exists("uploads"):
    os.makedirs("uploads")
else:
    # Clear all files in uploads directory on app launch
    # https://www.tutorialspoint.com/How-to-delete-all-files-in-a-directory-with-Python
    for root, dirs, files in os.walk("uploads"):
        for file in files:
            os.remove(os.path.join(root, file))

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

userActivities = {}

apis = {
    'strava': networks.strava.StravaApi(config, flaskApp)
}

# Index page
@flaskApp.route('/')
def render_index():
    # Render homepage with userdata if it exists
    sessionDataValidationResult = functions.validUserData(session)

    if sessionDataValidationResult == True: # User already logged in, redirect to parameters page
	    return redirect(url_for("render_parameters"))
    elif sessionDataValidationResult == False: # No user ID, not logged in.
        networks = {}
        for networkName in apis:
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

    # Wipe user image
    if "userData" in session and "id" in session["userData"] and "networkName" in session:
        uniqueId = functions.uniqueUserId(session["networkName"], session["userData"]["id"])
        #userImages[uniqueId] = None
        userActivities[uniqueId] = None

    return redirect(url_for('render_index'))

@flaskApp.route('/parameters')
def render_parameters():
    sessionDataValidationResult = functions.validUserData(session)

    if sessionDataValidationResult == True:
        uniqueId = functions.uniqueUserId(session["networkName"], session["userData"]["id"])
        if len(userActivities[uniqueId]["activities"]) > 0:
            currentDate = datetime.now()
            currentDateStr = datetime.strftime(currentDate, "%Y-%m-%d")
            yearAgoTime = currentDate- timedelta(days = 365)
            yearAgoStr = datetime.strftime(yearAgoTime, "%Y-%m-%d")
            return render_template("parameters.html", userData = session['userData'], activities = userActivities[uniqueId]["activities"], startDate = yearAgoStr, endDate = currentDateStr)
        else:
            return functions.throwError("No activities found in your account.")
    elif sessionDataValidationResult == False: # No userdata, render guest homepage
        return redirect(url_for("render_index"))
    else: # error thrown
        return sessionDataValidationResult

@flaskApp.route('/errorPage')
def render_errorPage():
    errorMessage = request.args.get("errorMsg")
    if errorMessage == None:
        errorMessage = "Unknown Error"

    return render_template("errorPage.html", errorMessage = errorMessage)

@flaskApp.route('/generatePage', methods = ["POST"])
def render_generatePage():
    # default values of form arguments
    formArgs = {
        "backgroundColor": (255,255,255),
        "backgroundImage": "",
        "blurIntensity": 5,
        "pathThickness": 5,
        "pathColor": (0,0,0),
        "displayGridLines": False,
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

    #print(request.form)
    #print("\n")
    #print(formArgs)
        
    if "userData" in session:
        if "id" in session["userData"]:
            if "networkName" in session:
                uniqueId = functions.uniqueUserId(session["networkName"], session["userData"]["id"])
                selected = dict([(activityID, userActivities[uniqueId]["activities"][activityID]) for activityID in userActivities[uniqueId]["activities"] if str(activityID) in formArgs["selectedActivities"]])
                if len(selected) > 0:
                    polylines = apis[session["networkName"]].getAllPolylines(selected)
                    filename = ""
                    if "backgroundImage" in request.files:
                        file = request.files['backgroundImage']

                        if file and functions.allowed_file(file.filename, ALLOWED_EXTENSIONS):
                            filename = secure_filename(file.filename)
                            file.save(os.path.join(flaskApp.config['UPLOAD_FOLDER'], filename))

                    return render_template("generatePage.html", visualization = functions.getImageBase64String(generateVis.getVis(data=polylines, lineThickness=int(formArgs["pathThickness"]), gridOn=formArgs["displayGridLines"] == "on", backgroundColor=formArgs["backgroundColor"], backgroundImage = filename, backgroundBlur = formArgs["blurIntensity"], foregroundColor=formArgs["pathColor"], gridColor=formArgs["gridlineColor"], gridThickness=int(formArgs["gridThickness"]), infoText=formArgs["infoText"], textBackgroundFade=formArgs["textBackgroundFade"], totalTime=userActivities[uniqueId]["timeElapsed"], totalDistance=userActivities[uniqueId]["distanceTravelled"])))
                else:
                    return functions.throwError("No activities were selected.")
    else:
        print("FAILED")
    return functions.throwError("Could not display visualized image.")

@flaskApp.route("/activityFiltering.js")
def returnActivityFiltering():
    return send_file("./static/activityFiltering.js")

@flaskApp.route("/fileVerification.js")
def returnFileVerification():
    return send_file("./static/fileVerification.js")

@flaskApp.route("/dynamicParameters.js")
def returnDynamicParameters():
    return send_file("./static/dynamicParameters.js")

@flaskApp.route('/aboutPage')
def render_aboutPage():
    sessionDataValidationResult = functions.validUserData(session)

    if sessionDataValidationResult == True:
        return render_template('aboutPage.html', userData = session['userData'])
    else:
        return render_template('aboutPage.html')

@flaskApp.route('/privacyPage')
def render_privacyPage():
    sessionDataValidationResult = functions.validUserData(session)

    if sessionDataValidationResult == True:
        return render_template('privacyPage.html', userData = session['userData'])
    else:
        return render_template('privacyPage.html')

# Store any config items not related to API logins under app.config
for key in config["DEFAULT"]:
    flaskApp.config[key] = config["DEFAULT"][key]