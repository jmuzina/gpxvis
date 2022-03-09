# App launch-point

# ---- Dependency imports ---- #
from flask import Flask, request, render_template, session, redirect, url_for
import json
import urllib.request
import urllib.parse
import requests
from flask_assets import Environment, Bundle
from configparser import RawConfigParser, ConfigParser
from os.path import exists
import time
import math
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
    # /strava-login?client_id=4732184&client_secret=xxxxx&code=5435789345   
    query_string = urllib.parse.urlencode( params )    

    data = query_string.encode( "ascii" )    
    
    if (authCode != ""):
        # Send authorization token for requests requiring authentication
        with requests.get(url, data = data, headers = {"Authorization": "Bearer " + authCode}) as response:
            return response
    else:
        with urllib.request.urlopen( url, data ) as response:     
            return json.loads(response.read())

class StravaApi:
    def __init__(self):
        # Configure strava-specific connection details
        self.configCode = 'strava'
        self.configDetails = config[self.configCode]
        self.tokenUrl = self.configDetails['TOKEN_URL'].strip('\'')
        self.clientId = self.configDetails['CLIENT_ID'].strip('\'')
        self.clientSecret = self.configDetails['CLIENT_SECRET'].strip('\'')

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

            # Testing: get user activities
            getActivities()
            
            # Render homepage
            return redirect(url_for('render_index'))

        # TESTING FUNCTION: prints out list of a user's activities
        @app.route('/' + self.configCode + '-getActivities')
        def getActivities():
            # Endpoint: https://developers.strava.com/docs/reference/#api-Activities-getLoggedInAthleteActivities
            # Strava requires that a "before" timestamp is included to filter activities. All activities logged before calltime will be printed.
            activitiesResponse = getAPI(url = "https://www.strava.com/api/v3/athlete/activities", authCode = session['userData']['accessKey'], params = {"before": str(math.floor(time.time()))})

            # Array of user SummaryActivities: https://developers.strava.com/docs/reference/#api-models-SummaryActivity
            activities = json.loads(activitiesResponse.content)
            print("Index", "\t", "Activity ID")
            for activityIndex in range(len(activities)):
                print(activityIndex, "\t", activities[activityIndex]['id']),
                #activityGPX = getAPI(url = "https://www.strava.com/api/v3/routes/" + str(activities[activityIndex]['id']) + "/export_gpx", authCode = session['userData']['accessKey'])
                try:
                    activityResponse = getAPI(url = "https://www.strava.com/api/v3/activities/" + str(activities[activityIndex]['id']), authCode = session['userData']['accessKey'], params = {"include_all_efforts": True})
                    activity = json.loads(activityResponse.json())
                    print("Activity: ", activity)
                    polyline = activity["map"]
                    print("polyline", polyline)
                except Exception as e:
                    print(e)
                    pass
                   
stravaApiHandler = StravaApi()

# Index page
@app.route('/')
def render_index():
    # Render homepage with userdata if it exists
    try:
        return render_template("index.html", cfg=config, userData = session['userData'])
    except: # No userdata, render guest homepage
        return render_template("index.html", cfg=config)

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