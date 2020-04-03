from flask import Flask, request
from flask_cors import CORS
import json
import requests
import decimal
from asterisk.ami import AMIClient, AMIClientAdapter, AutoReconnect, SimpleAction
import time
import sys
import logging


logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s\n')

app = Flask(__name__)

ami_ip = "192.168.180.253"
ami_port = 5038
ami_user = 'admin'
ami_secret='amipassword'

HEADERS = {"Access-Control-Allow-Origin": "*", "Access-Control-Allow-Methods": "POST", "Access-Control-Allow-Headers": "Content-Type"}

@app.route('/make_call')
def make_call():
    channel = request.args.get('channel', '')
    exten = request.args.get('exten', '')
    channel = '304'
    exten = '8' + exten[1:]

    user_client = AMIClient(address=ami_ip, port=ami_port)

    future = user_client.login(username=ami_user, secret=ami_secret)

    time.sleep(0.5)

    user_adapter = AMIClientAdapter(user_client)

    res = user_adapter.Originate(Channel='SIP/'+channel, Context='local', Exten=exten, ActionID=exten, Priority=1,  CallerID=exten, CallerIDName=exten, Timeout='')
        
    time.sleep(0.2)

    user_client.logoff()

    return  'ok', 200, HEADERS

CORS(app, support_credentials=True)

HOST = '0.0.0.0'
PORT = 8090

app.run(HOST, PORT, threaded=True) 

