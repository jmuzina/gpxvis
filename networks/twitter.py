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
import tweetImage
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

        # Handle twitter authentication. When users successfully log in to twitter, they are sent to {site-url}/twitter-login
        @app.route('/' + self.configCode + '-login')
        def twitterAuth():
            print(self.callbackUrl)
            uniqueId = functions.uniqueUserId(main.session["networkName"], main.session["userData"]["id"])
            main.userCachedData[uniqueId]["twitterOAuth"] = tweepy.OAuth1UserHandler(
                self.CONSUMER_KEY, self.CONSUMER_SECRET,
                callback=self.callbackUrl
            )
            return redirect(main.userCachedData[uniqueId]["twitterOAuth"].get_authorization_url(signin_with_twitter=True))

        @app.route("/twitter-login-callback")
        def twitterLoginCallback():
            uniqueId = functions.uniqueUserId(main.session["networkName"], main.session["userData"]["id"])
            main.session["twitterAccessToken"], main.session["twitterAccessTokenSecret"] = main.userCachedData[uniqueId]["twitterOAuth"].get_access_token(
                request.args["oauth_verifier"]
            )
            api = tweepy.API(main.userCachedData[uniqueId]["twitterOAuth"])
            main.userCachedData[uniqueId]["twitterOAuth"] = None
            user = self.getAuthenticatedUser()
            main.session["twitterUserID"] = user["id"]
            main.session["visualizationID"] = self.uploadImage()
            tweetID = self.postTweet()
            return redirect(url_for('render_generatePage', twitterUsername = user["username"], tweetID = tweetID))

    # Upload visualization to Twitter server and return media ID
    def uploadImage(self):
        uniqueId = functions.uniqueUserId(main.session["networkName"], main.session["userData"]["id"])
        if "twitterUserID" in main.session and uniqueId in main.userCachedData and "visualizationResult" in main.userCachedData[uniqueId]:
            twitterAPI = OAuth1Session(client_key=self.CONSUMER_KEY, client_secret=self.CONSUMER_SECRET, resource_owner_key=self.ACCESS_TOKEN_PUBLIC, resource_owner_secret=self.ACCESS_TOKEN_SECRET)
            postResult = twitterAPI.post(url="https://upload.twitter.com/1.1/media/upload.json", 
                data={
                    "media_data": main.userCachedData[uniqueId]["visualizationResult"][22:],
                    "media_category": "tweet_image",
                    "additional_owners":  main.session["twitterUserID"]
                }
            ).json()
            if "media_id_string" in postResult:
                main.session["twitterUserID"] = None
                return postResult["media_id_string"]

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
        tweetResult = self.getClient().create_tweet(media_ids=[main.session["visualizationID"]], text="Check out my GPX visualization! https://capstone3.cs.kent.edu", user_auth=True)
        main.session["visualizationID"] = None

        data = None
        
        for key in tweetResult:
            data = key
            break

        return data["id"]

        
    def isAvailable(self):
        return (functions.checkTimeout(url = self.tokenUrl) != False)
