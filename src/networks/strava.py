# ---- Dependency imports ---- #
import binascii
import math
import os
import time
from flask import redirect, request, url_for
import functions
import polyline
import app as main
import datetime
# ---------------------------- #
class StravaApi:
    def __init__(self, app):
        # Configure strava-specific connection details
        self.configCode = 'strava'
        self.tokenUrl = 'https://www.strava.com/oauth/token'.strip('\'')
        self.clientId = os.getenv('STRAVA_CLIENT_ID').strip('\'')
        self.clientSecret = os.getenv('STRAVA_CLIENT_SECRET').strip('\'')
        self.authUrl = "www.strava.com/oauth/authorize?client_id={client_id}&response_type=code&redirect_uri={app_address}/strava-login&approval_prompt=auto&scope=read,activity:read".format(client_id=os.getenv('STRAVA_CLIENT_ID'), app_address=os.getenv('APP_ADDRESS') or 'http://localhost').strip('\'')
        self.verifyToken = str(binascii.hexlify(os.urandom(24)))[2:-1]
        self.loginWith = True


        # Handle Strava authentication. When users successfully log in to Strava, they are sent to {site-url}/strava-login
        @app.route('/' + self.configCode + '-login')
        def stravaAuth():
            # Get user data and access token
            authResponse = functions.callAPI(url = self.tokenUrl, method="POST", params = {
                "client_id": self.clientId, 
                "client_secret": self.clientSecret, 
                "code": request.args.get('code')
            }).json()
            # Store user data as session for future use
            main.session["userData"] = authResponse["athlete"]
            main.session["accessKey"] = authResponse["access_token"]
            main.session["networkName"] = self.configCode

            uniqueId = functions.uniqueUserId(self.configCode, authResponse["athlete"]["id"])

            # Store user activities
            main.userCachedData[uniqueId] = self.getActivitiesInRange()

            print(main.userCachedData[uniqueId])

            if len(main.userCachedData[uniqueId]) > 0:            
                # Render parameters page
                return redirect(url_for('render_parameters'))
            else:
                main.userCachedData[uniqueId] = None
                return functions.throwError("There are no activities recorded on your Strava account.")
    
    def getAllPolylines(self, activities):
        decodedPolylines = []
        if activities == None:
            activities = self.getActivitiesInRange()

        for activityID in activities:
            if activities[activityID]["polyline"] != None and activities[activityID]["polyline"] != "":
                decodedPolylines.append(polyline.decode(activities[activityID]["polyline"]))

        return decodedPolylines

    def getActivitiesInRange(self, beforeTime = str(math.floor(time.time())), endTime = str(0)):
        activities = {}
        # Endpoint: https://developers.strava.com/docs/reference/#api-Activities-getLoggedInAthleteActivities
        # Strava requires that a "before" timestamp is included to filter activities. All activities logged before calltime will be printed.

        pageNum = 1 # Current "page" of results
        #activitiesFound = 0 # Used to print number of activities found, could have more uses later?
        #totalDistance = 0
        #totalTime = 0
        
        # Array of user SummaryActivities: https://developers.strava.com/docs/reference/#api-models-SummaryActivity
        # Get activities in batches of 100 until all have been found
        activitiesResponse = functions.callAPI(method="GET", url = "https://www.strava.com/api/v3/athlete/activities?before=" + beforeTime + "&after=" + endTime + "&per_page=200&page=" + str(pageNum), header = {"Authorization": "Bearer " + main.session['accessKey']}).json()
        while activitiesResponse != None:
            # Process batch if it is not empty
            if len(activitiesResponse) != 0:
                #print(str(pageNum) + "\tID\t\t", "Data")

                for activityIndex in range(len(activitiesResponse)):
                    if activitiesResponse[activityIndex]["map"]["summary_polyline"] != None:
                        #activitiesFound += 1

                        dto = datetime.datetime.strptime(activitiesResponse[activityIndex]["start_date_local"],'%Y-%m-%dT%H:%M:%SZ')
                        activities[activitiesResponse[activityIndex]["id"]] = {
                            "name":  activitiesResponse[activityIndex]["name"],
                            "polyline": activitiesResponse[activityIndex]["map"]["summary_polyline"],
                            "displayTime": dto.strftime('%m/%d/%Y'),
                            "duration": activitiesResponse[activityIndex]["moving_time"],
                            "type": activitiesResponse[activityIndex]["type"],
                            "distance": round(functions.metersToMiles(activitiesResponse[activityIndex]["distance"]), 2)
                        }

                        #totalDistance += activitiesResponse[activityIndex]["distance"]
                        #totalTime += activitiesResponse[activityIndex]["moving_time"]

                        #print("\t" + str(activitiesResponse[activityIndex]["id"]) + "\t", result[activitiesResponse[activityIndex]["id"]])

                # Advance to next page
                pageNum += 1
                activitiesResponse = functions.callAPI(method="GET", url = "https://www.strava.com/api/v3/athlete/activities?before=" + beforeTime + "&after=" + endTime + "&per_page=100&page=" + str(pageNum), header = {"Authorization": "Bearer " + main.session['accessKey']}).json()

            # No activities in the batch; exit the loop and return result
            else:
                activitiesResponse = None

        #print("Activity API calls needed:\t" + str(pageNum - 1) + "\nActivities found:\t" + str(activitiesFound))
        #averageDistance = totalDistance / activitiesFound
        #averageTime = totalTime / activitiesFound
        #totalTimeStr = str(datetime.timedelta(seconds = totalTime))
        #totalTimeStr = functions.getTimeStr(seconds = totalTime)
        #numHours = math.floor(((totalTime / 60) / 60))
        #numMinutes = math.floor(totalTime / 60)
        #totalDistanceStr = str(round(functions.metersToMiles(totalDistance), 2)) + " mi."

        #print("TIMESTR", totalTime, totalTimeStr, functions.getTimeStr(259200))

        return {
            "activities": activities, 
            #"timeElapsed": totalTimeStr, 
            #"distanceTravelled": totalDistanceStr
        }

    def isAvailable(self):
        return (functions.checkTimeout(url = self.tokenUrl) != False)
