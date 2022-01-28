# App launch-point

# ---- Dependency imports ---- #
from flask import Flask, request, render_template, session, redirect, url_for
import json
import urllib.request
import urllib.parse
from flask_assets import Environment, Bundle
from configparser import RawConfigParser, ConfigParser
# ---------------------------- #

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
config.readfp(open(r'./app.cfg'))
# -------------------------------------------- #

session = {} # Clear session on server reboot

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

# Load every supported login network and define routes for them based on cfg file
for cfgSectionName in config:
    if cfgSectionName != "DEFAULT":
        @app.route('/'+cfgSectionName+'-login')
        def login():
            # Assemble POST headers using auth code returned from API
            params = {    
                "client_id": config[cfgSectionName]['CLIENT_ID'].strip('\''),    
                "client_secret": config[cfgSectionName]['CLIENT_SECRET'].strip('\''),    
                "code": request.args.get('code'),
                "grant_type" : "authorization_code"
            }
                
            query_string = urllib.parse.urlencode( params )    
            data = query_string.encode( "ascii" )    
            
            # Send user auth code, app credentials to API to request their details
            with urllib.request.urlopen( config[cfgSectionName]['TOKEN_URL'].strip('\''), data ) as response:     
                response = json.loads(response.read())
                session['userData'] = response['athlete'] # Store session data
                return redirect(url_for('render_index'))
    else:
        # Store any config items not related to API logins under app.config
        for x in config[cfgSectionName]:
            app.config[x] = config[cfgSectionName]