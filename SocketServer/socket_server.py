from socketserver import TCPServer, ThreadingMixIn, BaseRequestHandler
from datetime import datetime, date
import _thread
import time
from flask import Flask, request
from flask_cors import CORS
import json
import sys
import logging
import tftpy
import uuid
from flask import send_file


logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s\n')

ones_serv = None

app = Flask(__name__)

HEADERS = {"Access-Control-Allow-Origin": "*", "Access-Control-Allow-Methods": "POST", "Access-Control-Allow-Headers": "Content-Type"}

users_phones = {}


class ThreadedTCPServer(ThreadingMixIn, TCPServer):
    pass

class OnesSocketServerHandler(BaseRequestHandler):
    def handle(self):
        self.callback(self.server, self.request, self.client_address)

class OnesSocketServer():
    handler = OnesSocketServerHandler
    users = {}

    def __init__(self):
        self.handler.callback = self.callback

    def callback(self, server, request, client_address):
        logging.info(f"""CONNECTED LISTENER {client_address}""")

        u_ref = None

        while True:
            try:
                buf = request.recv(256).decode('utf-8')
            except:
                break

            logging.info(f"""{client_address} recv -> {buf}""")

            if not buf: 
                break

            buf = buf.strip('\n')
            if buf == 'logout': 
                break
            elif buf[0:5] == 'u_ref' and len(buf[6:]) > 1:
                u_ref = buf[6:]
               
                u_ref = u_ref.upper()

                if self.users.get(u_ref) is None:
                    self.users[u_ref] = {}

                self.users[u_ref][client_address] = request


        logging.info(f"""DISCONNECTED LISTENER {client_address}""")
    
        if not u_ref is None:
            user = self.users.get(u_ref)

            if not user is None:
                sock = user[client_address]
                if not sock is None:
                    if sock._closed != True:
                        sock.close()
                    del user[client_address]

            if len(user) == 0:
                del self.users[u_ref]

def send_data_user(user, data, user_ref):
    if user is None:
        logging.info(f"""user not found -> {user_ref}""")
        return

    if len(user)==0:
        logging.info(f"""len(user) == 0 -> {user_ref}""")
        return

    user_save = user.copy()

    for x in user_save:
        sock = user_save[x]

        if sock._closed:
            logging.info(f"""sock closed {user_ref}""")
            continue
            
        sock.sendall(data.encode('utf-8'))

        logging.info(f"""sock sent -> {user_ref} {data}""")

        time.sleep(0.1)

@app.route('/user/send')
def user_send():
    user_ref = request.args.get('user', '').upper()
    data = request.args.get('data', '')

    for u in ones_serv.users:
        if u==user_ref:
            user = ones_serv.users.get(user_ref)
            try:
                send_data_user(user, data, user_ref)
            except:
                pass

    return  'ok', 200, HEADERS

@app.route('/user/reg_phone')
def user_reg_phone():
    user_ref = request.args.get('user', '').upper()
    phone = request.args.get('phone', '')

    if len(phone)>0:
        users_phones[phone] = user_ref

    return  'ok', 200, HEADERS

@app.route('/user/get_phone')
def user_get_phone():
    phone = request.args.get('phone', '')

    user = users_phones.get(phone)

    if user is None:
        user = {}

    return json.dumps(user), 200, HEADERS

@app.route('/users/ringing')
def users_call():
    data = request.args.get('data', '')

    data = json.loads(data)

    event_data = {'ref':data.get('event'), 'event':'ringing'}
    event_data = json.dumps(event_data)

    for u_phone in users_phones:
        for u in ones_serv.users:
            if u==users_phones[u_phone]:
                user = ones_serv.users.get(u)
                try:
                    send_data_user(user, event_data, u)
                except:
                    pass

    return 'ok', 200, HEADERS

@app.route('/users/call_up')
def users_call_up():
    data = request.args.get('data', '')

    data = json.loads(data)

    #Bridge->{'Privilege': 'call,all', 'Bridgestate': 'Link', 'Bridgetype': 'core', 'Channel1': 'SIP/trunk-sim1-00000c1e', 'Channel2': 'SIP/301-00000c20', 'Uniqueid1': '1579242940.3113', 'Uniqueid2': '1579242942.3115', 'CallerID1': '+79044987783', 'CallerID2': '620'}

    event_data = {'unique_id':data.get('Uniqueid1'), 'event':'call_up'}
    event_data = json.dumps(event_data)

    phone = data['Channel2'][4:7]

    for u_phone in users_phones:
        if u_phone!=phone:
            continue

        for u in ones_serv.users:
            #if u==users_phones[u_phone]:
            user = ones_serv.users.get(u)
            try:
                send_data_user(user, event_data, u)
            except:
                pass

    return 'ok', 200, HEADERS

@app.route('/calls/recordings')
def calls_recordings():
    path = request.query_string.decode('utf-8')
    path = path[:-5]

    options = {'blksize':512*32}

    tclient = tftpy.TftpClient('192.168.180.253', 70, options)

    file_name = str(uuid.uuid4())+'.wav'

    try:
        tclient.download(path, f'recordings/{file_name}')
    except Exception as e:
        logging.info(str(e))

    return send_file(f'recordings/{file_name}', attachment_filename=file_name)

def start_socket_server():
    while True:
        server.serve_forever()

TCP_IP = '0.0.0.0'
TCP_PORT = 11000

ones_serv = OnesSocketServer()
server = ThreadedTCPServer((TCP_IP, TCP_PORT), OnesSocketServerHandler)
    
logging.info('starting ones socket server '+str(TCP_IP)+':'+str(TCP_PORT)+' (use <Ctrl-C> to stop)')
_thread.start_new_thread(start_socket_server, ())

CORS(app, support_credentials=True)

HTTP_HOST = '0.0.0.0'
HTTP_PORT = 8099

app.run(HTTP_HOST, HTTP_PORT, threaded=True) 

