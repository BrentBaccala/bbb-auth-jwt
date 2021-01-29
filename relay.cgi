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

CONF_FILE='/etc/bigbluebutton/bbb-auth-jwt'
exec(open(CONF_FILE).read())

JWT = os.environ['PATH_INFO'][1:]

def ec2():
    global ec2_handle
    if ec2_handle == None:
        session=boto3.Session(region=AWS_REGION)
        ec2_handle = session.client('ec2')
    return ec2_handle

def is_remote_running():
    result = ec2().describe_instance_status(InstanceIds=[REMOTE_INSTANCE_LIST[0]], IncludeAllInstances=True)
    return result['InstanceStatuses'][0]['InstanceState']['Name'] == 'running'

def wait_for_remote():
    while True:
        try:
            requests.get(REMOTE_CHECK_URL, timeout=TIMEOUT)
            break
        except requests.ConnectTimeout:
            pass

def start_remote_if_needed():
    if not is_remote_running():
        ec2().start_instances(InstanceIds=REMOTE_INSTANCE_LIST)
        wait_for_remote()

try:
    jwt_options = {'require_exp' : True}
    jwt_algorithms = ['HS256']
    decoded = jwt.decode(jwt = JWT, key = JWT_KEY,
                         options = jwt_options,
                         algorithms = jwt_algorithms)

    start_remote_if_needed()

    response = REMOTE_LOGIN_URL + JWT
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
