# App launch-point

# ---- Dependency imports ---- #
import binascii
import json
import math
import os
import random
import socket
import time
import urllib.parse
import urllib.request
from configparser import ConfigParser, RawConfigParser
from datetime import datetime, timedelta
from os.path import exists
from socket import timeout

import gpxpy.gpx
import pandas as pd
import polyline
import requests
from flask import (Flask, Response, redirect, render_template, request,
                   session, url_for)
from flask_assets import Bundle, Environment

import functions
# ---------------------------- #

IS_SERVER = exists("/etc/letsencrypt/live/capstone3.cs.kent.edu/fullchain.pem") and exists("/etc/letsencrypt/live/capstone3.cs.kent.edu/privkey.pem")

flaskApp = Flask(__name__)
flaskApp.config['TEMPLATES_AUTO_RELOAD'] = True
# Hex-encoded random 24 character string for session encryption
flaskApp.config['SECRET_KEY'] = binascii.hexlify(os.urandom(24))

# ---- Bundle all scss files into all.css ---- #
assets     = Environment(flaskApp)
assets.url = flaskApp.static_url_path
scss       = Bundle('style.scss', filters='pyscss', output='all.css')
assets.config['SECRET_KEY'] = 'secret!'
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

import networks.strava # Must be imported after config has been read
       
apis = {
    'strava': networks.strava.StravaApi()
}

# Index page
@flaskApp.route('/')
def render_index():
    # Render homepage with userdata if it exists
    sessionDataValidationResult = functions.validUserData()

    if sessionDataValidationResult == True:
        return render_template("index.html", userData = session['userData'])
    elif sessionDataValidationResult == False: # No user ID, not logged in
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
    for k, v in session:
        session.pop(k)

    return redirect(url_for('render_index'))

@flaskApp.route('/parameters')
def render_parameters():
    sessionDataValidationResult = functions.validUserData()

    if sessionDataValidationResult == True:
        return render_template("parameters.html", userData = session['userData'])
    else: # No userdata, render guest homepage
        return sessionDataValidationResult

@flaskApp.route('/errorPage')
def render_errorPage(errorMsg="Unknown error"):
    return render_template("errorPage.html", errorMessage = errorMsg)

@flaskApp.route('/generatePage')
def render_generatePage():
    return render_template("generatePage.html")

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
