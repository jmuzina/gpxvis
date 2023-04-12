# GPX Visualizer

## Features
* **Activity import**: Authenticate with Strava or load activities from GPX files
* **Activity filtering**: Filter activities by date, activity type, and other attributes
* **Generate custom images**: Turn your activities into images with custom color, background, and style!
------------------
## Building
- Install python dependencies: `pip install -r requirements.txt`
- Set environment variables (.env):
  - `APP_ADDRESS`: Base address of the application where it is being served. If unset, the app will use `http://127.0.0.1:5000`.
  - Strava auth data (see [Developer Dashboard](https://www.strava.com/settings/api))
    - `STRAVA_CLIENT_ID`: Strava OAUTH Client ID
    - `STRAVA_CLIENT_SECRET`: Strava OAUTH Client Secret
- Run Flask locally: `python3 -m flask run`