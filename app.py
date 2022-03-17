# App launch-point

# ---- Dependency imports ---- #
import binascii
import json
import math
import os
import time
import random
import socket
import urllib.parse
import urllib.request
from configparser import ConfigParser, RawConfigParser
from datetime import datetime, timedelta
from os.path import exists
import polyline
from socket import timeout

import gpxpy.gpx
import pandas as pd
import requests
from flask import Flask, redirect, render_template, request, session, url_for, Response
from flask_assets import Bundle, Environment

import generateVis

# ---------------------------- #
IS_SERVER = exists("/etc/letsencrypt/live/capstone3.cs.kent.edu/fullchain.pem") and exists("/etc/letsencrypt/live/capstone3.cs.kent.edu/privkey.pem")
#APP_ADDRESS = urllib.request.urlopen('https://ident.me').read().decode('utf8')
#INTERNAL_ADDRESS = str(socket.gethostbyname(socket.gethostname()))

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True
# Hex-encoded random 24 character string for session encryption
app.config['SECRET_KEY'] = binascii.hexlify(os.urandom(24))

# ---- Bundle all scss files into all.css ---- #
assets     = Environment(app)
assets.url = app.static_url_path
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

session = {} # Clear session on server reboot

def uniqueUserId(networkName, idNum):
    return networkName + "-" + str(idNum)

# Return the results of an HTTP GET request to a specified URL
# authCode (str): an API access key for inclusion in the request header
# params (list): a list of items to be included in the request `data` section required by some API endpoints
def getAPI(url, authCode = "", params = {}):     
    # convert parameters into a query string. I.E. {"id": 2, "index": 5} -> ?id=2&index=5 
    query_string = urllib.parse.urlencode( params )    
    data = query_string.encode( "ascii" )    
    
    if (authCode != ""):
        # Send authorization token for requests requiring authentication
        with requests.get(url, data = data, headers = {"Authorization": "Bearer " + authCode}) as response:
            return response
    else:
        try:
            #raise timeout() # throw timeout error for debugging
            with urllib.request.urlopen( url, data, timeout = 3 ) as response:     
                return json.loads(response.read())
        # Used for checking network availability: If generic HTTP error returned, network is available
        except urllib.error.HTTPError as e:
            return True
        # Network API did not respond in time
        except timeout:
            return False

class StravaApi:
    def __init__(self):
        # Configure strava-specific connection details
        self.configCode = 'strava'
        self.configDetails = config[self.configCode]
        self.tokenUrl = self.configDetails['TOKEN_URL'].strip('\'')
        self.clientId = self.configDetails['CLIENT_ID'].strip('\'')
        self.clientSecret = self.configDetails['CLIENT_SECRET'].strip('\'')
        self.authUrl = self.configDetails['AUTH_URL'].strip('\'')
        self.verifyToken = str(binascii.hexlify(os.urandom(24)))[2:-1]

        # Handle Strava authentication. When users successfully log in to Strava, they are sent to {site-url}/strava-login
        @app.route('/' + self.configCode + '-login')
        def auth():
            # Get user data and access token
            authResponse = getAPI(url = self.tokenUrl, params = {
                "client_id": self.clientId, 
                "client_secret": self.clientSecret, 
                "code": request.args.get('code')
            })
            uniqueId = uniqueUserId(self.configCode, authResponse['athlete']['id'])
            # Store user data as session for future use
            session[uniqueId] = {
                "userData": authResponse["athlete"],
                #"authCode": request.args.get("code"),
                "accessKey": authResponse["access_token"]
            }
            session[uniqueId]["activities"] = self.getAllActivities(uniqueId) # Must be called after session is set

            # Store debugging visualization result as B64 string to display it without storing
            #session['userData']['imageBytes'] = "data:image/png;base64," + generateVis.getVis(self.getAllPolylines())

            #response.set_cookie("uid", uniqueUserId(self.configCode, authResponse['athlete']['id']), max_age=3600)
            
            # Render parameters page
            return redirect(url_for('render_parameters', uid = uniqueId))
    
    def getAllPolylines(self):
        result = []
        # Endpoint: https://developers.strava.com/docs/reference/#api-Activities-getLoggedInAthleteActivities
        # Strava requires that a "before" timestamp is included to filter activities. All activities logged before calltime will be printed.
        beforeTime = str(math.floor(time.time()))

        pageNum = 1 # Current "page" of results
        activitiesFound = 0 # Used to print number of activities found, could have more uses later?

        decodedPolylines = []

        # Array of user SummaryActivities: https://developers.strava.com/docs/reference/#api-models-SummaryActivity
        # Get activities in batches of 100 until all have been found
        activitiesResponse = getAPI(url = "https://www.strava.com/api/v3/athlete/activities?before=" + beforeTime + "&per_page=200&page=" + str(pageNum), authCode = session['userData']['accessKey']).json()
        while activitiesResponse != None:
            # Process batch if it is not empty
            if len(activitiesResponse) != 0:
                activitiesFound += len(activitiesResponse)
                print(str(pageNum) + "\tID\t\tName")

                for activityIndex in range(len(activitiesResponse)):
                    summary_polyline = activitiesResponse[activityIndex]["map"]["summary_polyline"]
                    if summary_polyline != None:
                        #print("summary for ", activitiesResponse[activityIndex]['name'])
                        #print(summary_polyline)
                        decodedPolylines.append(polyline.decode(summary_polyline))

                # Advance to next page
                pageNum += 1
                activitiesResponse = getAPI(url = "https://www.strava.com/api/v3/athlete/activities?before=" + beforeTime + "&per_page=100&page=" + str(pageNum), authCode = session['userData']['accessKey']).json()

            # No activities in the batch; exit the loop and return result
            else:
                activitiesResponse = None

        print(decodedPolylines)

        print("Activity API calls needed:\t" + str(pageNum - 1) + "\nActivities found:\t" + str(activitiesFound))
        return decodedPolylines

    def getAllActivities(self, uid):
        result = {}
        # Endpoint: https://developers.strava.com/docs/reference/#api-Activities-getLoggedInAthleteActivities
        # Strava requires that a "before" timestamp is included to filter activities. All activities logged before calltime will be printed.
        beforeTime = str(math.floor(time.time()))

        pageNum = 1 # Current "page" of results
        activitiesFound = 0 # Used to print number of activities found, could have more uses later?

        # Array of user SummaryActivities: https://developers.strava.com/docs/reference/#api-models-SummaryActivity
        # Get activities in batches of 100 until all have been found
        activitiesResponse = getAPI(url = "https://www.strava.com/api/v3/athlete/activities?before=" + beforeTime + "&per_page=200&page=" + str(pageNum), authCode = session[uid]['accessKey']).json()
        while activitiesResponse != None:
            # Process batch if it is not empty
            if len(activitiesResponse) != 0:
                activitiesFound += len(activitiesResponse)
                print(str(pageNum) + "\tID\t\tName")

                for activityIndex in range(len(activitiesResponse)):
                    result[activitiesResponse[activityIndex]['id']] = activitiesResponse[activityIndex]

                # Advance to next page
                pageNum += 1
                activitiesResponse = getAPI(url = "https://www.strava.com/api/v3/athlete/activities?before=" + beforeTime + "&per_page=100&page=" + str(pageNum), authCode = session[uid]['accessKey']).json()

            # No activities in the batch; exit the loop and return result
            else:
                activitiesResponse = None

        print("Activity API calls needed:\t" + str(pageNum - 1) + "\nActivities found:\t" + str(activitiesFound))
        return result

    def isAvailable(self):
        return (getAPI(url = self.tokenUrl) != False)
       
apis = {
    'strava': StravaApi()
}

def validUserData(args):
    if args.get('uid') != None:
        if args.get('uid') in session:
            if 'userData' in session[args.get('uid')]:
                return True
            else:
                return redirect(url_for("render_errorPage",  uid = request.args.get('uid'), errorMsg = "UserData was not found in session data."))
        else:
            return redirect(url_for("render_errorPage", errorMsg = "Invalid User ID"))
    return False


# Index page
@app.route('/')
def render_index():
    # Render homepage with userdata if it exists
    sessionDataValidationResult = validUserData(request.args)

    if sessionDataValidationResult == True:
        return render_template("index.html", userData = session[request.args.get('uid')]['userData'])
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

@app.route('/logout')
def logout():
    if request.args.get('uid') != None:
        session.pop(request.args.get('uid')) # Clear user session data

    return redirect(url_for('render_index'))

@app.route('/parameters')
def render_parameters():
    sessionDataValidationResult = validUserData(request.args)

    if sessionDataValidationResult == True:
        return render_template("parameters.html", userData = session[request.args.get('uid')]['userData'])
    else: # No userdata, render guest homepage
        return sessionDataValidationResult

@app.route('/errorPage')
def render_errorPage(errorMsg="Unknown error"):
    return render_template("errorPage.html", errorMessage = errorMsg)

@app.route('/generatePage')
def render_generatePage():
    return render_template("generatePage.html")

# Store any config items not related to API logins under app.config
for key in config["DEFAULT"]:
    app.config[key] = config["DEFAULT"][key]

# Launch VM server if applicable
if IS_SERVER:
    print("Starting KSU VM server...")
    app.run(host='capstone3.cs.kent.edu', port=443, ssl_context=('/etc/letsencrypt/live/capstone3.cs.kent.edu/fullchain.pem', '/etc/letsencrypt/live/capstone3.cs.kent.edu/privkey.pem'))
# elif (__name__ == "__main__"):
#     print("[ERROR]\tRunning from local copy, please launch the webserver with 'python -m flask run --host=" + INTERNAL_ADDRESS + "'")
#     print("\tWe now need to specify --host for Strava webhooks to function properly.\n\tYou may also need to open port 5000 on your router.\n")
