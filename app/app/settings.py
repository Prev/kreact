import sys
import os

# API Server settings
FLASK_APP_HOST = '0.0.0.0'
FLASK_APP_PORT = 8080

DEBUG = True


####################################
# Redis connection information
####################################
REDIS_HOST = os.environ.get('REDIS_HOST', 'localhost')
REDIS_PASS = os.environ.get('REDIS_PASS', '')
REDIS_DB = os.environ.get('REDIS_DB', 0)


if len(sys.argv) >= 2:
	FLASK_APP_PORT = int(sys.argv[1])