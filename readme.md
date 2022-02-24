# KSU Activity Art
 
# Linux Environment Setup
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

# Windows Environment Setup
Terminal commands in this section can be executed in Windows Powershell or Microsoft Visual Studio Code.
- Download [Python](https://www.python.org/downloads/).
- Download virtualenv: `pip3 install --user virtualenv`
- Create virtual environment: `python -m virtualenv CapstoneVenv`
- Activate virtual environment: `CapstoneVenv/Scripts/activate.bat`
- Clone repo: `git clone https://github.com/joemuzina/capstone`
- Install Flask & its dependencies
  - `pip3 install flask` (MAKE NOTE of where the command window says this package is installed).
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
- Open Capstone project folder: `cd Capstone`
- Run web server using the flask executable. In my case, this was at `C:\Users\JoeMuzina\AppData\Roaming\Python\Python37\Scripts\flask.exe`: `C:\Users\JoeMuzina\AppData\Roaming\Python\Python37\Scripts\flask.exe run` < should start the webserver.
