#!/usr/bin/python3
# Requires: sudo pip3 install requests
#
import socket
import requests
import json
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

haToken = "MY-HA-API-TOKEN"                                 # Set your HomeAssistant API Token
whUrl = 'https://X.X.X.X:8123/api/webhook/wh-snapmakera350' # Set to your HomeAssistant WebHook URL
bufferSize = 1024
msg = b'discover'
destPort = 20054
sockTimeout = 1.0
retries = 5
retryCounter = 0
snReply = {}

# Main Program
def main():
    UDPClientSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
    UDPClientSocket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    UDPClientSocket.settimeout(sockTimeout)
    
    checkState(UDPClientSocket,msg,destPort,retries)
    postIt(snReply)

# Check status of Snapmaker 2.0
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

# POST to HomeAssistant Webhook
def postIt(state):
  session = requests.Session()
  session.verify = False
  print("Sending State: ", state)
  try:
      requests.post(whUrl, json = state, verify=False)
  except requests.exceptions.ConnectionError:
      print("Could not connect to HomeAssistant on", whUrl)
      return

# Run Main Program
main()
