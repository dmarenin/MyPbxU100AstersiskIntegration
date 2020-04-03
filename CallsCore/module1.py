import tftpy

tclient = tftpy.TftpClient('192.168.180.253', 70)


file_name = '20200320174512-Inbound-sim1-+79969461327-620(301).wav'

file_from =f'/media/ysDisk_1/autorecords/20200320/{file_name}'

tclient.download('/media/ysDisk_1/autorecords/20200402/20200402124435-Inbound-sim3-79258416080-620(302).wav', f'recordings/865128d0-3461-449b-a8d3-6e2cc0c7c051.wav')


