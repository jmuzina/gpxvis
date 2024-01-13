# ---- Dependency imports ---- #
import json
import os
import random
import shutil
import time
import urllib.parse
import urllib.request
import math
from socket import timeout

import requests
from flask import (Flask, Response, redirect, render_template, request,
                   session, url_for)

import app as main

# ---------------------------- #

# Keys that may be stored in the session dict
sessionVars = ["accessKey", "networkName", "userData", "twitterAccessToken", "twitterUserID", "visualizationID"]

def allowed_file(filename, extensions):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in extensions

def getTimeStr(seconds):
    seconds = int(seconds)
    hours = int(math.floor(seconds / 60 / 60))
    mins = int(math.floor((seconds / 60) % 60))
    secs = int(math.floor(seconds % 60))

    hoursStr = str(hours)
    if hours < 10:
        hoursStr = "0" + hoursStr
    
    minsStr = str(mins)
    if mins < 10:
        minsStr = "0" + minsStr

    secsStr = str(secs)
    if secs < 10:
        secsStr = "0" + secsStr

    return hoursStr + ":" + minsStr + ":" + secsStr

def getImageBase64String(imageData):
    return "data:image/png;base64," + str(imageData)

def uniqueUserId(networkName, idNum):
    return networkName + "-" + str(idNum)

def metersToMiles(meters):
    return meters / 1609.344

# Return time since 1/1/1970
def epoch():
    return int(time.time())

# https://stackoverflow.com/questions/2511222/efficiently-generate-a-16-character-alphanumeric-string
def randomAlphanumericString(length = 16):
    return ''.join(random.choice('0123456789ABCDEF') for i in range(length))

# Return the results of an HTTP GET request to a specified URL
# authCode (str): an API access key for inclusion in the request header
# params (list): a list of items to be included in the request `data` section required by some API endpoints
def callAPI(url, method, params = {}, header = None):     
    method = method.lower()
    func = None

    if method == "post":
        func = requests.post
    elif method == "get":
        func = requests.get

    if func is not None:
        # convert parameters into a query string. I.E. {"id": 2, "index": 5} -> ?id=2&index=5 
        query_string = urllib.parse.urlencode( params )    
        data = query_string.encode( "ascii" )    

        if (header != None):
            # Send authorization token for requests requiring authentication
            with func(url, data = data, headers = header) as response:
                return response
        else:
            with func(url, data = data) as response:
                return response
    else:
        print("INVALID METHOD SUPPLIED", method)

def checkTimeout(url, timeToWait = 3):
    try:
        with urllib.request.urlopen(url, timeout = timeToWait) as response:     
            return json.loads(response.read())
    # Used for checking network availability: If generic HTTP error returned, network is available
    except urllib.error.HTTPError as e:
        return True, e
    # Network API did not respond in time
    except timeout:
        return False

def throwError(msg):
    return redirect(url_for("render_errorPage", errorMsg = msg))

def validUserData(session):
    if 'userData' in session:
        if 'accessKey' in session and "networkName" in session:
                return True
        else:
            return throwError(msg = "Incomplete session data")

    return False

# Wipe all data from user session
def wipeSession(session):
    sessionDataValidationResult = validUserData(session)

    if sessionDataValidationResult == True or ("networkName" in session and session["networkName"] == "gpxFile"):
        uniqueId = uniqueUserId(session["networkName"], session["userData"]["id"])
        if "sessionTimer" in main.userCachedData[uniqueId]:
            main.userCachedData[uniqueId]["sessionTimer"] = None

        # Delete GPX files
        if os.path.exists("uploads/" + uniqueId):
            shutil.rmtree("uploads/" + uniqueId)

    for key in sessionVars:
        if key in session:
            session.pop(key)
