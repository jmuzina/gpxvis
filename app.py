# App launch-point

# ---- Dependency imports ---- #
import os
from configparser import ConfigParser, RawConfigParser
from os.path import exists

from flask import (Flask, Response, redirect, render_template, request,
                   session, url_for)
from flask_assets import Bundle, Environment

import functions
import generateVis
# ---------------------------- #

IS_SERVER = exists("/etc/letsencrypt/live/capstone3.cs.kent.edu/fullchain.pem") and exists("/etc/letsencrypt/live/capstone3.cs.kent.edu/privkey.pem")

flaskApp = Flask(__name__)
flaskApp.config['TEMPLATES_AUTO_RELOAD'] = True
# Hex-encoded random 24 character string for session encryption
flaskApp.secret_key = os.urandom(32)

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
userImages = {}
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
        userImages[uniqueId] = None
        userActivities[uniqueId] = None

    return redirect(url_for('render_index'))

@flaskApp.route('/parameters')
def render_parameters():
    sessionDataValidationResult = functions.validUserData(session)

    if sessionDataValidationResult == True:
        uniqueId = functions.uniqueUserId(session["networkName"], session["userData"]["id"])
        if uniqueId in userActivities:
            print(userActivities[uniqueId])
            return render_template("parameters.html", userData = session['userData'], activities = userActivities[uniqueId])
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

@flaskApp.route('/generatePage')
def render_generatePage():
    if "userData" in session:
        if "id" in session["userData"]:
            if "networkName" in session:
                uniqueId = functions.uniqueUserId(session["networkName"], session["userData"]["id"])
                if uniqueId in userImages:
                    return render_template("generatePage.html", visualization = userImages[uniqueId])
    return functions.throwError("Could not display visualized image.")

# Store any config items not related to API logins under app.config
for key in config["DEFAULT"]:
    flaskApp.config[key] = config["DEFAULT"][key]

# Launch VM server if applicable
if IS_SERVER:
    print("Starting KSU VM server...")
    flaskApp.run(host='capstone3.cs.kent.edu', port=443, ssl_context=('/etc/letsencrypt/live/capstone3.cs.kent.edu/fullchain.pem', '/etc/letsencrypt/live/capstone3.cs.kent.edu/privkey.pem'))
# elif (__name__ == "__main__"):
#     print("[ERROR]\tRunning from local copy, please launch the webserver with 'python -m flask run --host=" + INTERNAL_ADDRESS + "'")
#     print("\tWe now need to specify --host for Strava webhooks to function properly.\n\tYou may also need to open port 5000 on your router.\n")
