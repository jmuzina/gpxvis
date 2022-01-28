# KSU Activity Art
 
# Environmnt Setup
- Clone repo: `git clone https://github.com/joemuzina/capstone`
- Install Python dependencies
  - Python3 venv: `apt install python3.8-venv`
  - VirtualEnv: `sudo apt-get install python3-virtualenv`
  - Python3: `sudo apt-get install python3`
- Create venv
  - `python3 -m venv venv/`
  - `.venv/bin/activate`
- Install Flask & its dependencies
  - `pip3 install flask`
  - `pip3 install flask`
  - `pip3 install Flask-Assets`
  - `pip3 install pyscss`
  - `pip3 install configparser`
  - `pip3 install requests`
- Complete app.cfg
  - Log in to the shared Strava account. The app API tokens/etc. are in the [API dashboard](https://www.strava.com/settings/api).
  - In `AUTH_URL`: replace `{ID}` with the Client ID from the dashboard
  - Replace `CLIENT_ID` with the Client ID from the dashboard
  - Replace `CLIENT_SECRET` with the Client Secret from the dashboard
  - Replace `SECRET_KEY` with a random string, whatever you like. 
- Run web server: `flask run`
