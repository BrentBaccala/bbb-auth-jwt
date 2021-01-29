#! /usr/bin/python3
#
# A CGI script used to authenticate users into Big Blue Button using a
# JSON web token.
#
# In addition to the standard JWT claims 'sub' (Subject) and 'exp'
# (expiration time, which is required), we also require 'role'
# (either 'm' for moderator or 'v' for viewer).
#
# Optional claim: 'mtg' for meeting ID (default is hostname)
#
# Moderators will start the meeting when they enter.  Viewers will
# get an error message if the meeting isn't already running.

import os
import re
import jwt
import socket
from vnc_collaborate import bigbluebutton

JWT = os.environ['PATH_INFO'][1:]

# These passwords don't have to be very secure because the API key
# is what really protects everything.  If you have the API key
# can get these passwords from the meeting's XML data anyway.

moderatorPW = 'jidtyv7RG8g0gsGMLq5M'
attendeePW = 'aQxdAAEi2fQq27TB6rTf'

# maps first letter of 'role' claim to the join password to be used
role_password = {'m' : moderatorPW,
                 'a' : attendeePW,
                 'v' : attendeePW,
}

def securitySalt():
    with open('/usr/share/bbb-web/WEB-INF/classes/bigbluebutton.properties') as prop_file:
        for line in prop_file:
            match = re.match('securitySalt=(.*)', line)
            if match:
                return match.group(1)
    return None

try:
    jwt_options = {'require_exp' : True}
    jwt_algorithms = ['HS256']
    decoded = jwt.decode(jwt = JWT, key = securitySalt(),
                         options = jwt_options,
                         algorithms = jwt_algorithms)
    fullName = decoded['sub']
    if 'mtg' in decoded:
        meetingID = decoded['mtg']
    else:
        meetingID = socket.gethostname()
    roomName = meetingID

    password = role_password[decoded['role'].lower()[0]]

    # This API call will quietly fail if the meeting is already running.
    if password == moderatorPW:
        voiceBridge = 1 + hash(meetingID)%65534
        response = bigbluebutton.APIcall('create', {'name': roomName,
                                                    'meetingID': meetingID,
                                                    'attendeePW': attendeePW,
                                                    'moderatorPW': moderatorPW,
                                                    'isBreakoutRoom': False
        })

    response = bigbluebutton.API_URL('join', {'meetingID': meetingID,
                                              'fullName': fullName,
                                              'password': password,
                                              'redirect': 'true'
    })
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
