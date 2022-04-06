# ---- Dependency imports ---- #
import json
import math
import urllib.parse
import urllib.request
from socket import timeout

import requests
from flask import (Flask, Response, redirect, render_template, request,
                   session, url_for)

# ---------------------------- #

def allowed_file(filename, extensions):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in extensions

def getImageBase64String(imageData):
    return "data:image/png;base64," + str(imageData)

def uniqueUserId(networkName, idNum):
    return networkName + "-" + str(idNum)

def metersToMiles(meters):
    return meters / 1609.344

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

def throwError(msg):
    return redirect(url_for("render_errorPage", errorMsg = msg))

def validUserData(session):
    if 'userData' in session:
        if 'accessKey' in session:
                return True
        else:
            return throwError(msg = "Access key was not found in session data.")

    return False

def wipeSession(session):
    for k, v in session:
        session.pop(k)
