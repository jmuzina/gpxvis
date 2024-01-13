import sys
import logging
logging.basicConfig(stream=sys.stderr)

from app import flaskApp as application
flaskApp = application