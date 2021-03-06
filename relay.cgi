#! /usr/bin/python3
#
# A CGI script used to authenticate relay users from a login system
# into an AWS-based Big Blue Button system using a JSON web token.
#
# If the JWT validates properly, the script will check if the
# Big Blue Button system is running, start it if not, then
# relay the connection using an HTTP redirect.
#
# In particular, expired tokens don't validate and won't start
# the Big Blue Button system.
#
# TODO:
# Moderators will start the meeting when they enter.  Viewers will
# get an error message if the meeting isn't already running.

import os
import jwt
import requests
import socket
import boto3
import urllib

CONF_FILE='/etc/bigbluebutton/bbb-auth-jwt'
exec(open(CONF_FILE).read())

WAIT_URL = 'https://' + socket.getfqdn() + '/wait.html'

JWT = os.environ['PATH_INFO'][1:]

ec2_handle = None

def ec2():
    global ec2_handle
    if ec2_handle == None:
        session = boto3.Session(region_name = AWS_REGION)
        ec2_handle = session.client('ec2')
    return ec2_handle

def is_remote_running():
    result = ec2().describe_instance_status(InstanceIds=[REMOTE_INSTANCE_LIST[0]], IncludeAllInstances=True)
    return result['InstanceStatuses'][0]['InstanceState']['Name'] == 'running'

def start_remote():
    ec2().start_instances(InstanceIds=REMOTE_INSTANCE_LIST)

try:
    jwt_options = {'require_exp' : True}
    jwt_algorithms = ['HS256']
    decoded = jwt.decode(jwt = JWT, key = JWT_KEY,
                         options = jwt_options,
                         algorithms = jwt_algorithms)

    if is_remote_running():
        response = REMOTE_LOGIN_URL + JWT
    else:
        start_remote()
        response = WAIT_URL + '?' + urllib.parse.urlencode({'pingUrl' : 'https://itpietraining.com/',
                                                            'targetUrl' : REMOTE_LOGIN_URL + JWT})
    print(f"Location: {response}\n")


except Exception as ex:
    print(f"""Content-type: text/html

<HTML>
<HEAD>
<TITLE>Login Failed</TITLE>
</HEAD>
<BODY>
<CENTER><H3>Login Failed</H3></CENTER>

Something went wrong!

<PRE>
{repr(ex)}
</PRE>
</BODY>
</HTML>
""")
