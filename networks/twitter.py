# ---- Dependency imports ---- #
import base64
import binascii
import datetime
import math
import os
import time
import urllib
import app as main
import functions
import generateVis
import polyline
import requests
import tweepy
from flask import Flask, Response, redirect, render_template, request, url_for
from requests_oauthlib import OAuth1Session

# ---------------------------- #

class twitterApi:
    def __init__(self, cfg, app):
        # Configure twitter-specific connection details
        self.configCode = 'twitter'
        self.configDetails = cfg[self.configCode]
        self.tokenUrl = self.configDetails['TOKEN_URL'].strip('\'')
        self.authUrl = self.configDetails['AUTH_URL'].strip('\'')
        self.callbackUrl = self.configDetails['CALLBACK_URL'].strip('\'')
        self.CONSUMER_KEY = self.configDetails['CONSUMER_KEY'].strip('\'')
        self.CONSUMER_SECRET = self.configDetails['CONSUMER_SECRET'].strip('\'')
        self.ACCESS_TOKEN_PUBLIC = self.configDetails['ACCESS_TOKEN_PUBLIC'].strip('\'')
        self.ACCESS_TOKEN_SECRET = self.configDetails['ACCESS_TOKEN_SECRET'].strip('\'')
        self.loginWith = False

        # Share with twitter button
        @app.route('/' + self.configCode + '-login')
        def twitterAuth():
            sessionDataValidationResult = functions.validUserData(main.session)
            if sessionDataValidationResult == True or ("networkName" in main.session and main.session["networkName"] == "gpxFile"):
                uniqueId = functions.uniqueUserId(main.session["networkName"], main.session["userData"]["id"])

                # Authenticate our app with Twitter
                main.userCachedData[uniqueId]["twitterOAuth"] = tweepy.OAuth1UserHandler(
                    self.CONSUMER_KEY, self.CONSUMER_SECRET,
                    callback=self.callbackUrl
                )

                # Use authenticated session to generate secure Twitter login page URL and redirect the user
                return redirect(main.userCachedData[uniqueId]["twitterOAuth"].get_authorization_url(signin_with_twitter=True))
            # User is not logged in, render the homepage
            else:
                return redirect(url_for("render_index"))

        # Twitter sends users back to this route once they have finished authentication with args "oauth_code" and "oauth_verifier"
        @app.route("/twitter-login-callback")
        def twitterLoginCallback():
            sessionDataValidationResult = functions.validUserData(main.session)
            if sessionDataValidationResult == True or ("networkName" in main.session and main.session["networkName"] == "gpxFile"):
                uniqueId = functions.uniqueUserId(main.session["networkName"], main.session["userData"]["id"])
                if "twitterOAuth" in main.userCachedData[uniqueId]:
                    if uniqueId in main.userCachedData and "visualizationResult" in main.userCachedData[uniqueId]:
                        # Store twitter access tokens using the data twitter sends
                        main.session["twitterAccessToken"], main.session["twitterAccessTokenSecret"] = main.userCachedData[uniqueId]["twitterOAuth"].get_access_token(
                            request.args["oauth_verifier"]
                        )

                        # Start a user-context API session using the received access token
                        api = tweepy.API(main.userCachedData[uniqueId]["twitterOAuth"])

                        # Clear the OAuth handler as it is no longer needed
                        main.userCachedData[uniqueId]["twitterOAuth"] = None

                        # Get user info
                        user = self.getAuthenticatedUser()
                        main.session["twitterUserID"] = user["id"]

                        # Upload the generated visualization to Twitter's servers
                        imageUploadedSuccessfully, data = self.uploadImage()

                        # Image was successfully uploaded, store its ID
                        if imageUploadedSuccessfully:
                            main.session["visualizationID"] = data
                        # Image was not uploaded, return user to the relevant error page
                        else:
                            return data

                        # Post a tweet containing the visualized image
                        tweetID = self.postTweet()
                        return redirect(url_for('render_generatePage', twitterUsername = user["username"], tweetID = tweetID))
                    else:
                        return functions.throwError("No visualization found to share")
                else:
                    return functions.throwError("No Twitter authentication data was found")
            else:
                return redirect(url_for("render_index"))

    # Upload visualization to Twitter server and return media ID
    def uploadImage(self, attemptNumber=1):
        # Try a maximum of 3 times to upload the image
        if attemptNumber <= 3:
            sessionDataValidationResult = functions.validUserData(main.session)
            if sessionDataValidationResult == True or ("networkName" in main.session and main.session["networkName"] == "gpxFile"):
                uniqueId = functions.uniqueUserId(main.session["networkName"], main.session["userData"]["id"])
                if "twitterUserID" in main.session:
                    # Start an authenticated API session between our application and Twitter
                    twitterAPI = OAuth1Session(client_key=self.CONSUMER_KEY, client_secret=self.CONSUMER_SECRET, resource_owner_key=self.ACCESS_TOKEN_PUBLIC, resource_owner_secret=self.ACCESS_TOKEN_SECRET)
                    uploadResult = twitterAPI.post(url="https://upload.twitter.com/1.1/media/upload.json", 
                        data={
                            "media_data": main.userCachedData[uniqueId]["visualizationResult"][22:],
                            "media_category": "tweet_image",
                            "additional_owners":  main.session["twitterUserID"]
                        }
                    )
                    try:
                        uploadResultJSON = uploadResult.json()
                        # Upload the visualization to Twitter's servers and store its ID
                        if "media_id_string" in uploadResultJSON:
                            main.session["twitterUserID"] = None
                            return True, uploadResultJSON["media_id_string"]
                        else:
                            # Twitter servers are under high stress: attempt the upload again.
                            if uploadResult.status_code == 503:
                                return self.uploadImage(attemptNumber + 1)
                            else:
                                return False, functions.throwError("Failed to upload image to Twitter.")
                    except Exception as e:
                        if hasattr(e, "message"):
                            return False, functions.throwError(e.message)
                        else:
                            return False, functions.throwError("Failed to upload image to Twitter.")
                else:
                    return False, functions.throwError("No Twitter User ID found")
            else:
                return False, functions.throwError("Invalid session data")
        else:
            return False, functions.throwError("Twitter's media upload servers are currently under heavy stress. Please try again later or, save the image and upload it directly.")

    def getClient(self):
        return tweepy.Client(
            consumer_key=self.CONSUMER_KEY,
            consumer_secret=self.CONSUMER_SECRET,
            access_token=main.session["twitterAccessToken"],
            access_token_secret=main.session["twitterAccessTokenSecret"]
        )

    def getAuthenticatedUser(self, client=None):
        if client == None:
            client = self.getClient()

        me = client.get_me()
        for key in me:
            return key

    def postTweet(self):
        if "visualizationID" in main.session:
            client = self.getClient()
            if client:
                tweetResult = client.create_tweet(media_ids=[main.session["visualizationID"]], text="Check out my GPX visualization! https://capstone3.cs.kent.edu", user_auth=True)
                main.session["visualizationID"] = None

                data = None
                
                for key in tweetResult:
                    data = key
                    break

                return data["id"]

    def isAvailable(self):
        return (functions.checkTimeout(url = self.tokenUrl) != False)
