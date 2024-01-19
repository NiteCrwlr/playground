#!/usr/bin/python3
# Requires: sudo pip3 install requests
#
import socket
import requests
import json
import urllib3
import ipaddress
import time
from datetime import timedelta
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

haToken = "<hatoken>" # Set your HomeAssistant API Token
whUrl = 'https://<ipadress>:8123/api/webhook/wh-snapmakera350' # Set to your HomeAssistant WebHook URL
bufferSize = 1024
msg = b'discover'
destPort = 20054
sockTimeout = 1.0
retries = 5
retryCounter = 0
snReply = {}
connectIP = '';
tokenfile = '/home/pi/SmartHome/SnapMaker/SMtoken.txt' # Set to writable path, file will be created if not exists.

# Main Program
def main():
    global connectIP
    UDPClientSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
    UDPClientSocket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    UDPClientSocket.settimeout(sockTimeout)
    
    # Get Status and IP of Snapmaker
    checkState(UDPClientSocket,msg,destPort,retries)
    if validate_ip_address(snReply.get("ip")):
        connectIP = snReply.get("ip")
        print("Snapmaker found:", connectIP)
        SMtoken = getSMToken(connectIP)
        print("Connecting with Token:",SMtoken)
        postIt(readStatus(SMtoken))
        # Not yet used
        #readStatusEnclosure(SMtoken)
        
    else:
        print("No Snapmaker found.")
     

def getSMToken(connectIP):
    # Create file if not exists
    try:
        f = open(tokenfile, "r+")
    except FileNotFoundError:
        f = open(tokenfile, "w+")
        
    SMurl = "http://" + connectIP + ":8080/api/v1/connect"
    SMtoken = f.read()
    if SMtoken == "":
        # Create token
        connected = False
        while not connected:
            r = requests.post(SMurl)
            print("Please authorize on Touchscreen.")
            time.sleep(10)
            if "Failed" in r.text:
                print(r.text)
                print("Binding failed, please restart script")
                exit(1)
            SMtoken = (json.loads(r.text).get("token"))
            headers = {'Content-Type' : 'application/x-www-form-urlencoded'}
            formData = {'token' : SMtoken}
            r = requests.post(SMurl, data=formData, headers=headers)
            if json.loads(r.text).get("token") == SMtoken:
                f.write(SMtoken)
                print("Token received and saved.\nRestart Script for autoconnect now.")
                connected = True
                return(SMtoken)
                exit(0)
    
    else:
        f.close()
        # Connect to SnapMaker with saved token
        headers = {'Content-Type' : 'application/x-www-form-urlencoded'}
        formData = {'token' : SMtoken}
        r = requests.post(SMurl, data=formData, headers=headers)
        return(SMtoken)
        # Do keepalive
        #while True:
        #    r = requests.get(SMstatus+SMtoken)
        #    print(r.text)
        #    time.sleep(2)
        #    r = requests.get(SMenclosure+SMtoken)
        #    print(r.text)
        #    time.sleep(2)


# Read Status of Snapmaker 2.0 via API
# Example Data IDLE:
# {"status":"IDLE","x":112,"y":142,"z":150,"homed":false,"offsetX":0,"offsetY":0,"offsetZ":0,"toolHead":"TOOLHEAD_3DPRINTING_1",
# "nozzleTemperature":19,"nozzleTargetTemperature":0,"heatedBedTemperature":20,"heatedBedTargetTemperature":0,
# "isFilamentOut":false,"workSpeed":1500,"printStatus":"Idle",
# "moduleList":{"enclosure":true,"rotaryModule":false,"emergencyStopButton":true,"airPurifier":false},
# "isEnclosureDoorOpen":false,"doorSwitchCount":0}
#
# Example Data RUNNING:
# {"status":"RUNNING","x":-19,"y":339,"z":310.763,"homed":false,"offsetX":0,"offsetY":0,"offsetZ":0,"toolHead":"TOOLHEAD_3DPRINTING_1",
# "nozzleTemperature":63,"nozzleTargetTemperature":205,"heatedBedTemperature":20,"heatedBedTargetTemperature":70,
# "isFilamentOut":false,"workSpeed":1500,"printStatus":"Printing",
# "fileName":"Leon_Base.gcode","totalLines":20295,"estimatedTime":3204,"currentLine":91,"progress":0.004483863245695829,"elapsedTime":20,"remainingTime":3195,
# "moduleList":{"enclosure":true,"rotaryModule":false,"emergencyStopButton":true,"airPurifier":false},
# "isEnclosureDoorOpen":false,"doorSwitchCount":0}
#
def readStatus(SMtoken):
    #print("Reading SN Status...")
    SMstatus = "http://" + connectIP + ":8080/api/v1/status?token="
    r = requests.get(SMstatus+SMtoken)
    snStatus = json.loads(r.text).get("status")
    snNozzleTemp = json.loads(r.text).get("nozzleTemperature")
    snNozzleTaTemp = json.loads(r.text).get("nozzleTargetTemperature")
    snHeatedBedTemp = json.loads(r.text).get("heatedBedTemperature")
    snHeatedBedTaTemp = json.loads(r.text).get("heatedBedTargetTemperature")
    
    if json.loads(r.text).get("fileName") is not None:
        snFileName = json.loads(r.text).get("fileName") 
    else:
        snFileName = "N/A"
    if json.loads(r.text).get("progress") is not None:
        snProgress = ("{:0.1f}".format(json.loads(r.text).get("progress")*100))
    else:
        snProgress = "0"
    if json.loads(r.text).get("elapsedTime") is not None:
        snElapsedTime = str(timedelta(seconds=json.loads(r.text).get("elapsedTime")))
    else:
        snElapsedTime = "00:00:00"
    if json.loads(r.text).get("remainingTime") is not None:
        snRemainingTime = str(timedelta(seconds=json.loads(r.text).get("remainingTime")))
    else:
        snRemainingTime = "00:00:00"
    
    snReply = {"snIP":connectIP,"snStatus":snStatus,"snNozzleTemp":snNozzleTemp,"snNozzleTaTemp":snNozzleTaTemp,
               "snHeatedBedTemp":snHeatedBedTemp,"snHeatedBedTaTemp":snHeatedBedTaTemp,"snFileName":snFileName,
               "snProgress":snProgress,"snElapsedTime":snElapsedTime,"snRemainingTime":snRemainingTime}
    return(snReply)
  
# Read Status of Enclosure
# Example Data:
# {"isReady":true,"isDoorEnabled":false,"led":100,"fan":0}
#  
def readStatusEnclosure(SMtoken):
    print("Reading Enclosure Status...")
    SMenclosure = "http://" + connectIP + ":8080/api/v1/enclosure?token="
    r = requests.get(SMenclosure+SMtoken)
    print(r.text)
    return(r.text)
    

# Check status of Snapmaker 2.0 via UDP Discovery
# Possible replies:
#  'Snapmaker@X.X.X.X|model:Snapmaker 2 Model A350|status:IDLE'
#  'Snapmaker@X.X.X.X|model:Snapmaker 2 Model A350|status:RUNNING'
def checkState(UDPClientSocket,msg,destPort,retries):
    global snReply
    global retryCounter
    UDPClientSocket.sendto(msg, ("255.255.255.255", destPort))
    try:
        reply, server_address_info = UDPClientSocket.recvfrom(1024)
        elements = str(reply).split('|')
        snIP = (elements[0]).replace('\'','')
        snModel = (elements[1]).replace('\'','')
        snStatus = (elements[2]).replace('\'','')
        snIP, snIPVal = snIP.split('@')
        snModel, snModelVal = snModel.split(':')
        snStatus, snStatusVal = snStatus.split(':')
        snReply = {"ip":snIPVal, "model":snModelVal, "state":snStatusVal}
    except socket.timeout:
        retryCounter += 1
        if (retryCounter==retries): 
          snReply = {"ip":"N/A", "model":"N/A", "state":"OFFLINE"}
          return
        else:
          checkState(UDPClientSocket,msg,destPort,retries);
          
# Check if IP is valid:          
def validate_ip_address(ip_string):
   try:
       ip_object = ipaddress.ip_address(ip_string)
       return True
   except ValueError:
       return False

# POST to HomeAssistant Webhook
def postIt(state):
    session = requests.Session()
    session.verify = False
    print("Sending State:", state)
    try:
        requests.post(whUrl, json = state, verify=False)
    except requests.exceptions.ConnectionError:
        print("Could not connect to HomeAssistant on", whUrl)
        return

# Run Main Program
main()
