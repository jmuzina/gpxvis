# ---- Dependency imports ---- #
import binascii
import math
import os
import time
from flask import Flask, redirect, render_template, request, url_for, Response
import functions
import generateVis
import polyline
import app as main
# ---------------------------- #
class StravaApi:
    def __init__(self, cfg, app):
        # Configure strava-specific connection details
        self.configCode = 'strava'
        self.configDetails = cfg[self.configCode]
        self.tokenUrl = self.configDetails['TOKEN_URL'].strip('\'')
        self.clientId = self.configDetails['CLIENT_ID'].strip('\'')
        self.clientSecret = self.configDetails['CLIENT_SECRET'].strip('\'')
        self.authUrl = self.configDetails['AUTH_URL'].strip('\'')
        self.verifyToken = str(binascii.hexlify(os.urandom(24)))[2:-1]

        # Handle Strava authentication. When users successfully log in to Strava, they are sent to {site-url}/strava-login
        @app.route('/' + self.configCode + '-login')
        def auth():
            # Get user data and access token
            authResponse = functions.getAPI(url = self.tokenUrl, params = {
                "client_id": self.clientId, 
                "client_secret": self.clientSecret, 
                "code": request.args.get('code')
            })
            # Store user data as session for future use
            main.session["userData"] = authResponse["athlete"]
            main.session["accessKey"] = authResponse["access_token"]
            main.session["activities"] = self.getAllActivities() # Must be called after session is set
            main.session["networkName"] = self.configCode

            # Store debugging visualization result as B64 string to display it without storing
            main.userImages[functions.uniqueUserId(self.configCode, authResponse["athlete"]["id"])] = functions.getImageBase64String(generateVis.getVis(data=self.getAllPolylines()))
            
            # Render parameters page
            return redirect(url_for('render_parameters'))
    
    def getAllPolylines(self):
        result = []
        # Endpoint: https://developers.strava.com/docs/reference/#api-Activities-getLoggedInAthleteActivities
        # Strava requires that a "before" timestamp is included to filter activities. All activities logged before calltime will be printed.
        beforeTime = str(math.floor(time.time()))

        pageNum = 1 # Current "page" of results
        activitiesFound = 0 # Used to print number of activities found, could have more uses later?

        decodedPolylines = []

        # Array of user SummaryActivities: https://developers.strava.com/docs/reference/#api-models-SummaryActivity
        # Get activities in batches of 100 until all have been found
        activitiesResponse = functions.getAPI(url = "https://www.strava.com/api/v3/athlete/activities?before=" + beforeTime + "&per_page=200&page=" + str(pageNum), authCode = main.session['accessKey']).json()
        while activitiesResponse != None:
            # Process batch if it is not empty
            if len(activitiesResponse) != 0:
                activitiesFound += len(activitiesResponse)
                print(str(pageNum) + "\tID\t\tName")

                for activityIndex in range(len(activitiesResponse)):
                    summary_polyline = activitiesResponse[activityIndex]["map"]["summary_polyline"]
                    if summary_polyline != None:
                        #print("summary for ", activitiesResponse[activityIndex]['name'])
                        #print(summary_polyline)
                        decodedPolylines.append(polyline.decode(summary_polyline))

                # Advance to next page
                pageNum += 1
                activitiesResponse = functions.getAPI(url = "https://www.strava.com/api/v3/athlete/activities?before=" + beforeTime + "&per_page=100&page=" + str(pageNum), authCode = main.session['accessKey']).json()

            # No activities in the batch; exit the loop and return result
            else:
                activitiesResponse = None

        print(decodedPolylines)

        print("Activity API calls needed:\t" + str(pageNum - 1) + "\nActivities found:\t" + str(activitiesFound))
        return decodedPolylines

    def getAllActivities(self):
        result = {}
        # Endpoint: https://developers.strava.com/docs/reference/#api-Activities-getLoggedInAthleteActivities
        # Strava requires that a "before" timestamp is included to filter activities. All activities logged before calltime will be printed.
        beforeTime = str(math.floor(time.time()))

        pageNum = 1 # Current "page" of results
        activitiesFound = 0 # Used to print number of activities found, could have more uses later?

        # Array of user SummaryActivities: https://developers.strava.com/docs/reference/#api-models-SummaryActivity
        # Get activities in batches of 100 until all have been found
        activitiesResponse = functions.getAPI(url = "https://www.strava.com/api/v3/athlete/activities?before=" + beforeTime + "&per_page=200&page=" + str(pageNum), authCode = main.session['accessKey']).json()
        while activitiesResponse != None:
            # Process batch if it is not empty
            if len(activitiesResponse) != 0:
                activitiesFound += len(activitiesResponse)
                print(str(pageNum) + "\tID\t\tName")

                for activityIndex in range(len(activitiesResponse)):
                    result[activitiesResponse[activityIndex]['id']] = activitiesResponse[activityIndex]

                # Advance to next page
                pageNum += 1
                activitiesResponse = functions.getAPI(url = "https://www.strava.com/api/v3/athlete/activities?before=" + beforeTime + "&per_page=100&page=" + str(pageNum), authCode = main.session['accessKey']).json()

            # No activities in the batch; exit the loop and return result
            else:
                activitiesResponse = None

        print("Activity API calls needed:\t" + str(pageNum - 1) + "\nActivities found:\t" + str(activitiesFound))
        return result

    def isAvailable(self):
        return (functions.getAPI(url = self.tokenUrl) != False)
