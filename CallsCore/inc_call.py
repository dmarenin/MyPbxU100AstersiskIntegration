from asterisk.ami import AMIClient, AutoReconnect
import time
import json
import requests
import time
from requests.auth import HTTPBasicAuth
import sys
import logging
import pymysql.cursors
from datetime import datetime, date


db_host = '192.168.180.253'
db_user = 'admin'
db_pass='amipassword'
db = 'asteriskcdr'
db_port = 3306

black_list_events = ['ExtensionStatus', 'PeerStatus', 'Dial', 'Registry', 'QueueMemberStatus', 'NewAccountCode']

logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s\n')


def event_listener(event, **kwargs):
    try:
        do_handle_event(event.name, event.keys)
    except Exception as e:
        logging.info(str(e)+'   ->   '+str(event))

def do_handle_event(name, data):
    if name in black_list_events:
        return

    logging.info(name + '->' + str(data))

    #f = open('logs.log', 'a')
    #f.write(name + '->' + str(data) + '\n')
    #f.close()

    if name=='Newchannel':
        if data['Context']=='from-trunk':
            create_inbound_call(data)

    elif name=='Hangup':
        done_call(data)

    elif name=='Bridge':
        send_call_to_user(data)

    elif name=='Cdr':
        add_recordings(data)

def get_recordings_path(data):
    path = ''

    con = connection()
    if con is None:
        return None

    cursor = con.cursor()

    tbl = datetime.now().strftime("%Y%m")

    sql_text = f"""SELECT * FROM cdr_{tbl} WHERE uniqueid = '{data['UniqueID']}'"""

    result = do_query(cursor, sql_text)
    if len(result)==0:
        logging.info('recordings not found '+str(data['UniqueID']))
    else:
        path = result[0]['monitorpath']

    data['path'] = path

    cursor.close()

    con.close()

def connection():
    try:
        connection = pymysql.connect(host=db_host, port=db_port, user=db_user, password=db_pass, db=db, charset='utf8mb4', cursorclass=pymysql.cursors.DictCursor)
    except Exception as e:
        logging.info(e)
        return None

    return connection

def do_query(cursor, sql_text, val=None):
    try:
        res = cursor.execute(sql_text, )
    except Exception as e:
        logging.info(e)
        return None
        
    result = cursor.fetchall()

    return result

def add_recordings(data):
    get_recordings_path(data)

    call = {'UniqueID':data['UniqueID'], 'path':data['path']}

    value = json.dumps(call)

    r = s.get(f"""{http}/hs/gate/v1?method=add_recordings&data={value}""", headers=headers, auth=auth_ones)

    if r.status_code != 200:
        logging.info(str(r.reason)+' -> '+str(r.text))

def send_call_to_user(data):
    value = json.dumps(data)

    r = s.get(f"""{http_socket}/users/call_up?data={value}""")

    if r.status_code != 200:
        logging.info(str(r.reason)+' -> '+str(r.text))

def done_call(data):
    CallerIDNum = data.get('CallerIDNum')
    CallerIDName = data.get('CallerIDName')
    Uniqueid = data.get('Uniqueid')

    CallerIDNum = CallerIDNum[1:]

    if len(CallerIDNum)!=11:
        return

    call = {'CallerIDNum':CallerIDNum, 'CallerIDName':CallerIDName, 'UniqueID':Uniqueid}

    value = json.dumps(call)

    r = s.get(f"""{http}/hs/gate/v1?method=done_call&data={value}""", headers=headers, auth=auth_ones)

    if r.status_code != 200:
        logging.info(str(r.reason)+' -> '+str(r.text))

def create_inbound_call(data):
    CallerIDNum = data.get('CallerIDNum')
    CallerIDName = data.get('CallerIDName')
    Uniqueid = data.get('Uniqueid')

    CallerIDNum = CallerIDNum[1:]

    if len(CallerIDNum)!=11:
        return

    call = {'CallerIDNum':CallerIDNum, 'CallerIDName':CallerIDName, 'UniqueID':Uniqueid}

    value = json.dumps(call)

    r = s.get(f"""{http}/hs/gate/v1?method=init_call&data={value}""", headers=headers, auth=auth_ones)

    if r.status_code == 200:
        r = s.get(f"""{http_socket}/users/ringing?data={r.text}""")
    else:
        logging.info(str(r.reason)+' -> '+str(r.text))
    

ami_ip = "192.168.180.253"
ami_port = 5038
ami_user = 'admin'
ami_secret='amipassword'

headers = {'Content-type': 'application/json'}
http = 'http://192.168.180.150/umc'
auth_ones = HTTPBasicAuth('4', 'R')

http_socket = "http://192.168.180.150:8099"

s = requests.Session()

client = AMIClient(address=ami_ip, port=ami_port)

AutoReconnect(client)

try:
    future = client.login(username=ami_user, secret=ami_secret)
except:
    raise Exception('ami client login failed')

time.sleep(0.5)

if future.response.is_error():
    raise Exception(str(future.response))

client.add_event_listener(event_listener)

