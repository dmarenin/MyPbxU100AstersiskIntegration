import paramiko
import time
import sys
import logging


logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s\n')

host = '192.168.180.253'
user = 'root'
secret = 'ys123456'
port = 8022

while True:
    client = paramiko.SSHClient()
    
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, username=user, password=secret, port=port)
    stdin, stdout, stderr = client.exec_command('udpsvd -vE 0.0.0.0 70 tftpd /media/ysDisk_1/')
    data = stdout.read() + stderr.read()
    
    logging.info(data)
    
    client.close()

    time.sleep(5)

