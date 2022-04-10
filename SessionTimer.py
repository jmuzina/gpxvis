import functions
from flask import session
import app as main

TIME_LIMIT = 1800

class SessionTimer():
    def __init__(self):
        self.start()

    def start(self):
        self.startTime = functions.epoch()

    def timeElapsed(self):
        return (functions.epoch() - self.startTime)

    def expired(self):
        return self.timeElapsed() >= TIME_LIMIT