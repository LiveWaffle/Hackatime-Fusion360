import adsk.core
import adsk.fusion
app = adsk.core.Application.get()
ui = app.userInterface
import traceback
import hashlib
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'bundles'))

import time
import subprocess
import ctypes
import configparser
from subprocess import Popen, PIPE, STDOUT
from . import commands
from .lib import fusionAddInUtils as futil
import threading
import platform
def checkInstallDependencies():
    try:
        import requests
        import chardet
        log("Dependencies already installed...!")
    except ImportError:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "requests", "chardet"])
            log("Dependencies Installed...!")
        except Exception as e:
            log(f"Failed to install dependencies: {str(e)}")

if sys.platform == "win32":
    from subprocess import CREATE_NO_WINDOW
def checkInstallWindows():
    pypath = os.path.dirname(sys.executable)
    PyExe = os.path.join(pypath,"python","python.exe")
    exists = os.path.exists(pypath + "/Lib/site-packages/requests")

lastActive = time.time()
heartbeat_interval = 30
inactive_threshold = 30

def log(message, level=adsk.core.LogLevels.InfoLogLevel):
    if app:
        app.log(str(message))

def waitForDocument():
    while True:
        try:
            if app.activeDocument is not None:
                break
        except:
            pass
        log("Waiting For Document")
        time.sleep(1)
    log("Document Detected")
    Contents()

def getActiveDocument():
    try:
        folder = None
        design = None

        design= app.activeDocument
        if design:
            if design.dataFile:
                folder = design.dataFile.parentFolder
                if folder is None:
                    folder = design
            else:
                folder = design

    except Exception as e:
        log(f"Could not get Active Document: {e}")
    return [folder,design]

def update_activity():
    global lastActive
    lastActive = time.time()

stopEvent = threading.Event()

def run(context):
    try:
        if sys.platform == "win32":
            checkInstallWindows()
        elif sys.platform == "darwin":
            log("macOS")
            threading.Thread(target=waitForDocument, daemon=True).start()
            return
        Contents()
    except Exception as e:
        log(f"Run failed: {str(e)}")



def Contents():
    import chardet

    log("part -1")
    try:
        def DetectEncode():
            if sys.platform == "win32":
                configPath = os.path.join(os.environ['USERPROFILE'], '.wakatime.cfg')
            elif sys.platform == "darwin":
                configPath = os.path.join(os.environ['HOME'], '.wakatime.cfg')
            with open(configPath, "rb") as file:
                    data = file.read()
                    from chardet.universaldetector import UniversalDetector

                    def detect(data):
                        detector = UniversalDetector()
                        detector.feed(data)
                        detector.close()
                        return detector.result

                    encoded = detect(data)
                    encoding = encoded["encoding"]
                    if encoding is None:
                        return "UTF-8"
                    else:
                        return encoding
        DetectEncode()

        log(DetectEncode())
        log("part 1")
        parse=configparser.ConfigParser()
        if sys.platform == "win32":
            parsePath = os.path.join(os.environ['USERPROFILE'], '.wakatime.cfg')
        else:
            parsePath = os.path.join(os.environ['HOME'], '.wakatime.cfg')
        parse.read(parsePath, encoding=DetectEncode())

        if os.path.exists(parsePath):
            APIKEY = parse.get('settings','api_key')
            APIURL = parse.get('settings','api_url')
            log("Key: "+APIKEY + " Url: "+ APIURL)
        else:
            ErrorMessage = ctypes.windll.user32.MessageBoxW(0, u"Please use the script to download the hackatime files! https://hackatime.hackclub.com/", u"Invalid File", 0)

        arch = platform.machine()
        log(platform.machine())

        log("part 2")

        
        if platform == "linux" or platform == "linux2":
            log("Linux")
            if arch in ("AMD","x86_64"):
                WakaTimePath = os.path.join(os.path.dirname(__file__),"wakatime-clis", "wakatime-cli-linux-amd64")
            elif arch in ("i386", "i686", "x86"):
                WakaTimePath = os.path.join(os.path.dirname(__file__),"wakatime-clis", "wakatime-cli-linux-386")
            elif arch in ("ARM"):
                WakaTimePath = os.path.join(os.path.dirname(__file__), "wakatime-clis", "wakatime-cli-linux-arm")
            elif arch in ("ARM64", "aarch64"):
                WakaTimePath = os.path.join(os.path.dirname(__file__), "wakatime-clis", "wakatime-cli-linux-arm64")
            elif arch in ("RISCV64", "riscv64"):
                WakaTimePath = os.path.join(os.path.dirname(__file__), "wakatime-clis", "wakatime-cli-linux-riscv64")
            else:
                log("Unsupported Architecture")



        elif platform == "darwin":
            log("macOS")
            if arch in ("AMD","x86_64"):
                WakaTimePath = os.path.join(os.path.dirname(__file__), "wakatime-clis", "wakatime-cli-darwin-amd64")
            elif arch in ("ARM64", 'arm64'):
                WakaTimePath = os.path.join(os.path.dirname(__file__), "wakatime-clis", "wakatime-cli-darwin-arm64")



        elif sys.platform == "win32":
            log("Windows")
            if arch in "AMD64":
                WakaTimePath = os.path.join(os.path.dirname(__file__), "wakatime-clis", "WakaTimeCli.exe")
            elif arch in ("ARM64", "aarch64"):
                WakaTimePath = os.path.join(os.path.dirname(__file__), "wakatime-clis", "WakaTimeCliARM64.exe")
            elif arch in ("i386", "x86"):
                WakaTimePath = os.path.join(os.path.dirname(__file__), "wakatime-clis", "WakaTimeCli386.exe")
                        



        timeout = 30
        start_time = time.time()
        design = None


        data = getActiveDocument()

        log("FusionDocument type: " + str(design))

        url = "https://hackatime.hackclub.com/api/v1/my/heartbeats"

        log(url)

        
        lastKnownProjectName = "Untitled"
        lastKnownDesignName = "Untitled"

        def sendHeartBeat():
            getActiveDocument()
            global lastKnownProjectName
            global lastKnownDesignName
            folder, design = getActiveDocument()
            if folder:
                lastKnownProjectName = folder.name
            folderName = lastKnownProjectName
            
            if design:
                lastKnownDesignName = design.name
            designName = lastKnownDesignName

            
            if design and design.dataFile:
                versionNumber = f" v{design.dataFile.versionNumber}"
                designName = design.name.replace(versionNumber, '')
                


            timestamp = int(time.time())
            if time.time() - lastActive < inactive_threshold: 
                    CliCommand = [
                    WakaTimePath,
                    '--key', APIKEY,
                    '--entity', folderName,
                    '--time', str(timestamp),
                    '--write',
                    '--plugin', 'fusion360-wakatime/0.0.1',
                    '--alternate-project', designName,
                    '--category', "designing",
                    '--language', 'Fusion360',
                    '--is-unsaved-entity',
                    ]
                    try:
                        log("Running CLI: " + ' '.join(CliCommand))
                        if  sys.platform == "win32":
                            result = subprocess.run(CliCommand, capture_output=True, text=True, creationflags=CREATE_NO_WINDOW)
                        else:
                            result = subprocess.run(CliCommand, capture_output=True, text=True)
                        log(f"Heartbeat Sent under project: {folderName}")
                    except Exception as e:
                        log("error!!")
                        log("Error sending heartbeat: " + str(e))

            else:
                log("User Inactive")


        def handleUserInteractions(args):
            update_activity()


        def onCommandUse(args: adsk.core.ApplicationCommandEventArgs):
            update_activity()
            cmdID = args.commandId
            log(f'Command starting: {cmdID}')
        futil.add_handler(ui.commandStarting, onCommandUse)

        def looping():
            while not stopEvent.is_set():
                sendHeartBeat()
                time.sleep(heartbeat_interval)
        threading.Thread(target=looping,daemon=True).start()
    except Exception as e:
        log("Error when running!!!")
        log(e)
        

def stop():
    log("Shutting Fusion WakaTime down")
    futil.clear_handlers()
    stopEvent.set()

