#!/bin/sh
authbind gunicorn -w3 --reload -b 0.0.0.0:80 ledgerman:api
