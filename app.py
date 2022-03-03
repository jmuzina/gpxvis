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

def fetchApi(url, authCode = "", params = {}):        
    query_string = urllib.parse.urlencode( params )    
    data = query_string.encode( "ascii" )    
    
    if (authCode != ""):
        with requests.get(url, data = data, headers = {"Authorization": "Bearer " + authCode}) as response:
            return response
    else:
        with urllib.request.urlopen( url, data ) as response:     
            return json.loads(response.read())

class StravaApi:
    def __init__(self):
        self.configCode = 'strava'
        self.configDetails = config[self.configCode]
        self.tokenUrl = self.configDetails['TOKEN_URL'].strip('\'')
        self.clientId = self.configDetails['CLIENT_ID'].strip('\'')
        self.clientSecret = self.configDetails['CLIENT_SECRET'].strip('\'')

        # Strava Login route
        @app.route('/' + self.configCode + '-login')
        def auth():
            # Get user data and access token
            authResponse = fetchApi(url = self.tokenUrl, params = {
                "client_id": self.clientId, 
                "client_secret": self.clientSecret, 
                "code": request.args.get('code')
            })
            session['userData'] = authResponse['athlete']
            session['userData']['authCode'] = request.args.get('code')
            session['userData']['accessKey'] = authResponse['access_token']

            # Testing: get user activities
            getActivities()
            
            return redirect(url_for('render_index'))
            
        @app.route('/' + self.configCode + '-getActivities')
        def getActivities():
            activitiesResponse = fetchApi(url = "https://www.strava.com/api/v3/athlete/activities?before=" + str(math.floor(time.time())), authCode = session['userData']['accessKey'])
            print(activitiesResponse.content)
            
            
stravaApiHandler = StravaApi()

# Index page
@app.route('/')
def render_index():
    # Render homepage with userdata if it exists
    try:
        return render_template("index.html", cfg=config, userData = session['userData'])
    except:
        return render_template("index.html", cfg=config)

@app.route('/logout')
def logout():
    session.pop('userData') # Clear user session data
    return redirect(url_for('render_index'))

# Store any config items not related to API logins under app.config
for key in config["DEFAULT"]:
    app.config[key] = config["DEFAULT"][key]

if IS_SERVER:
    print("Starting KSU VM server...")
    app.run(host='capstone3.cs.kent.edu', port=443, ssl_context=('/etc/letsencrypt/live/capstone3.cs.kent.edu/fullchain.pem', '/etc/letsencrypt/live/capstone3.cs.kent.edu/privkey.pem'))
elif (__name__ == "__main__"):
    print("[ERROR]: Running from local copy, please launch the webserver with python -m flask run.")