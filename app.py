# App launch-point

# ---- Dependency imports ---- #
import json
import math
import time
import urllib.parse
import urllib.request
from configparser import ConfigParser, RawConfigParser
from datetime import datetime, timedelta
from os.path import exists
from socket import timeout

import gpxpy.gpx
import pandas as pd
import requests
from flask import Flask, redirect, render_template, request, session, url_for
from flask_assets import Bundle, Environment

import gpxTesting

# ---------------------------- #
IS_SERVER = exists("/etc/letsencrypt/live/capstone3.cs.kent.edu/fullchain.pem") and exists("/etc/letsencrypt/live/capstone3.cs.kent.edu/privkey.pem")

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True

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

        # Handle Strava authentication. When users successfully log in to Strava, they are sent to {site-url}/strava-login
        @app.route('/' + self.configCode + '-login')
        def auth():
            # Get user data and access token
            authResponse = getAPI(url = self.tokenUrl, params = {
                "client_id": self.clientId, 
                "client_secret": self.clientSecret, 
                "code": request.args.get('code')
            })
            # Store user data as session for future use
            session['userData'] = authResponse['athlete']
            session['userData']['authCode'] = request.args.get('code')
            session['userData']['accessKey'] = authResponse['access_token']

            # Store debugging visualization result as B64 string to display it without storing
            session['userData']['imageBytes'] = "data:image/png;base64," + gpxTesting.getVis(self.getAllGPX())
            
            # Render homepage
            return redirect(url_for('render_index'))

    def GPXFromDataStream(self, activityID, startTime):
        dataStream = getAPI(url = "https://www.strava.com/api/v3/activities/" + str(activityID) + "/streams?key_by_type=true&keys=time,distance,latlng,altitude", authCode = session['userData']['accessKey']).json()
        # Only allow visualization of activities with coordinate data
        if "latlng" in dataStream:
            dataFrame = pd.DataFrame([*dataStream["latlng"]["data"]], columns=['lat','long'])
            timestamps = []
            for secondsPassed in dataStream["time"]["data"]:
                timestamps.append(startTime + timedelta(seconds=secondsPassed))          

            dataFrame["time"] = timestamps
            dataFrame["altitude"] = dataStream["altitude"]["data"]

            gpx = gpxpy.gpx.GPX()
            gpx_track = gpxpy.gpx.GPXTrack()
            gpx.tracks.append(gpx_track)

            gpx_segment = gpxpy.gpx.GPXTrackSegment()
            gpx_track.segments.append(gpx_segment)

            for segmentIndex in range(len(dataStream["latlng"]["data"])):
                segment = gpxpy.gpx.GPXTrackPoint(dataStream["latlng"]["data"][segmentIndex][0], dataStream["latlng"]["data"][segmentIndex][1], dataStream["altitude"]["data"][segmentIndex], time=dataFrame["time"][segmentIndex])
                if segment != None:
                    gpx_segment.points.append(segment)

            return gpx.to_xml()
    
    def getAllGPX(self):
        result = []
        # Endpoint: https://developers.strava.com/docs/reference/#api-Activities-getLoggedInAthleteActivities
        # Strava requires that a "before" timestamp is included to filter activities. All activities logged before calltime will be printed.
        beforeTime = str(math.floor(time.time()))

        pageNum = 1 # Current "page" of results
        activitiesFound = 0 # Used to print number of activities found, could have more uses later?

        # Array of user SummaryActivities: https://developers.strava.com/docs/reference/#api-models-SummaryActivity
        # Get activities in batches of 100 until all have been found
        activitiesResponse = getAPI(url = "https://www.strava.com/api/v3/athlete/activities?before=" + beforeTime + "&per_page=100&page=" + str(pageNum), authCode = session['userData']['accessKey']).json()
        while activitiesResponse != None:
            # Process batch if it is not empty
            if len(activitiesResponse) != 0:
                activitiesFound += len(activitiesResponse)
                print(str(pageNum) + "\tID\t\tName")

                # Process each activity in the batch
                for activityIndex in range(len(activitiesResponse)):
                    print("\t" + str(activitiesResponse[activityIndex]['id']) + "\t" + activitiesResponse[activityIndex]['name'])

                    # Create an XML string in GPX format using the activitiy's data
                    xml = self.GPXFromDataStream(activitiesResponse[activityIndex]['id'], datetime.strptime(activitiesResponse[activityIndex]["start_date_local"], "%Y-%m-%dT%H:%M:%SZ"))
                    # Process only valid XML activities
                    if xml != None:
                        result.append(xml)

                # Advance to next page
                pageNum += 1
                activitiesResponse = getAPI(url = "https://www.strava.com/api/v3/athlete/activities?before=" + beforeTime + "&per_page=100&page=" + str(pageNum), authCode = session['userData']['accessKey']).json()

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

# Index page
@app.route('/')
def render_index():
    # Render homepage with userdata if it exists
    if 'userData' in session:
        return render_template("index.html", userData = session['userData'])
    else: # No userdata, render guest homepage
        networks = {}
        for networkName in apis:
            networkDetails = False
            if apis[networkName].isAvailable():
                networkDetails = apis[networkName].authUrl
            
            networks[networkName] = networkDetails

        return render_template("index.html", networks = networks)

@app.route('/logout')
def logout():
    session.pop('userData') # Clear user session data
    return redirect(url_for('render_index'))

# Store any config items not related to API logins under app.config
for key in config["DEFAULT"]:
    app.config[key] = config["DEFAULT"][key]

# Launch VM server if applicable
if IS_SERVER:
    print("Starting KSU VM server...")
    app.run(host='capstone3.cs.kent.edu', port=443, ssl_context=('/etc/letsencrypt/live/capstone3.cs.kent.edu/fullchain.pem', '/etc/letsencrypt/live/capstone3.cs.kent.edu/privkey.pem'))
elif (__name__ == "__main__"):
    print("[ERROR]: Running from local copy, please launch the webserver with python -m flask run.")
