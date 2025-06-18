import traceback
import hashlib
import os
import sys
import time
import subprocess
import ctypes
import configparser
import adsk.core
import adsk.fusion
from subprocess import Popen, PIPE, STDOUT
from subprocess import CREATE_NO_WINDOW
from . import commands
from .lib import fusionAddInUtils as futil
import threading
import requests

app = adsk.core.Application.get()
ui = app.userInterface
local_handlers = [] 


lastActive = time.time()
heartbeat_interval = 30
inactive_threshold = 30


parse=configparser.ConfigParser()
parsePath = os.path.join(os.environ['USERPROFILE'], '.wakatime.cfg')
parse.read(parsePath)

if os.path.exists(parsePath):
 APIKEY = parse.get('settings','api_key')
 APIURL = parse.get('settings','api_url')
 print("Key: "+APIKEY + " Url: "+ APIURL)
else:
    ErrorMessage = ctypes.windll.user32.MessageBoxW(0, u"Please use the script to download the hackatime files! https://hackatime.hackclub.com/", u"Invalid File", 0)

WakaTimePath = os.path.join(os.path.dirname(__file__), "WakaTimeCli.exe")

timeout = 30
start_time = time.time()


def getActiveDocument():
    try:
        design= app.activeDocument
        if design is not None:
            return design.name
    except Exception as e:
        app.log(f"Could not get Active Document: {e}")
        return None


design = getActiveDocument()
if not design:
    design = "Untitled"

app.log("FusionDocument type: " + str(design))


def update_activity():
    global lastActive
    lastActive = time.time()

url = "https://hackatime.hackclub.com/api/v1/my/heartbeats"

app.log(url)

def sendHeartBeat():
    timestamp = int(time.time())
    if time.time() - lastActive < inactive_threshold: 
            CliCommand = [
            WakaTimePath,
            '--key', APIKEY,
            '--entity', design,
            '--time', str(timestamp),
            '--write',
            '--plugin', 'fusion360-wakatime/0.0.1',
            '--alternate-project', design,
            '--category', "designing",
            '--language', 'Fusion360',
            '--is-unsaved-entity',
            ]
            try:
                app.log("Running CLI: " + ' '.join(CliCommand))
                result = subprocess.run(CliCommand, capture_output=True, text=True, creationflags=CREATE_NO_WINDOW)
                app.log("Heartbeat Sent.")

            except Exception as e:
                app.log("Error sending heartbeat: " + str(e))


    else:
        app.log("User Inactive")


def handleUserInteractions(args):
   update_activity()

def looping():
   sendHeartBeat()
   threading.Timer(heartbeat_interval, looping).start()


def onCommandUse(args: adsk.core.ApplicationCommandEventArgs):
    update_activity()
    cmdID = args.commandId
    app.log(f'Command starting: {cmdID}')
futil.add_handler(ui.commandStarting, onCommandUse)




looping()
