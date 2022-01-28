# apt install python3.8-venv
# sudo apt-get install python3-virtualenv
# sudo apt-get install python3
# python3 -m venv venv/
# . venv/bin/activate
# pip3 install flask
# pip3 install Flask-Assets
# pip3 install pyscss
# pip3 install configparser
# pip3 install requests

from flask import Flask, request, render_template, session, redirect, url_for
import json
import urllib.request
import urllib.parse
from flask_assets import Environment, Bundle
from configparser import RawConfigParser, ConfigParser

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True


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

configParser = RawConfigParser()   
configFilePath = r'./app.cfg'
configParser.read(configFilePath)

config = ConfigParser()
config.readfp(open(r'./app.cfg'))

session = {}

@app.route('/')
def render_index():
    try:
        return render_template("index.html", cfg=config, userData = session['userData'])
    except:
        return render_template("index.html", cfg=config)

@app.route('/logout')
def logout():
    session.pop('userData')
    return redirect(url_for('render_index'))

for cfgSectionName in config:
    if cfgSectionName != "DEFAULT":
        @app.route('/'+cfgSectionName+'-login')
        def login():
            params = {    
                "client_id": config[cfgSectionName]['CLIENT_ID'].strip('\''),    
                "client_secret": config[cfgSectionName]['CLIENT_SECRET'].strip('\''),    
                "code": request.args.get('code'),
                "grant_type" : "authorization_code"
            }
                
            query_string = urllib.parse.urlencode( params )    
            data = query_string.encode( "ascii" )    
                
            with urllib.request.urlopen( config[cfgSectionName]['TOKEN_URL'].strip('\''), data ) as response:     
                response = json.loads(response.read())
                session['userData'] = response['athlete']
                return redirect(url_for('render_index'))
    else:
        for x in config[cfgSectionName]:
            app.config[x] = config[cfgSectionName]