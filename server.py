from flask import Flask, jsonify, request
import requests
import time
import atexit
from apscheduler.schedulers.background import BackgroundScheduler
from os import walk
import socket
hostname = socket.gethostname()
IPAddr = socket.gethostbyname(hostname)

app = Flask(__name__)
ip_data={}
ip_port={}

def syncwithnodes():
    # print("chalu hogaya bhai")
    # print(filenames)
    # print(type(filenames))
    filenames = next(walk("data/"), (None, None, []))[2]  # [] if no file
    base_url = "http://"+hostname[:-2]+"{}"+".berry.scss.tcd.ie:33696/registernodes"
    data_payload=','.join(filenames)
    headers = {
    'Content-Type': 'text/plain'
    }
    for i in range(1, 50): # ip range
        try:
            # print("trying ip: ",base_url.format(i))
            response = requests.post(base_url.format(i), headers=headers, data=data_payload, timeout=1)
        except:
            n = 0
    print(ip_data)
    # print(ip_port)
    return True

@app.route('/checkalive', methods=['GET'])
def check_alive():
    # print(hostname, IPAddr)
    return jsonify({'message': '{} is alive!'.format("http://rasp-0"+str(IPAddr)[-2:]+".berry.scss.tcd.ie")}), 200

@app.route('/registernodes', methods=['POST'])
def register_node():
    if ("http://rasp-0"+str(request.remote_addr)[-2:]+".berry.scss.tcd.ie") not in ip_data or request.data.decode('UTF-8') not in ip_data.values():
        ip_data.update({"http://rasp-0"+str(request.remote_addr)[-2:]+".berry.scss.tcd.ie":request.data.decode('UTF-8')})
        print("Registered Node with IP: ",request.remote_addr)
    if ("http://rasp-0"+str(request.remote_addr)[-2:]+".berry.scss.tcd.ie") not in ip_port or request.environ['REMOTE_PORT'] not in ip_port.values():
        ip_port.update({"http://rasp-0"+str(request.remote_addr)[-2:]+".berry.scss.tcd.ie":request.environ['REMOTE_PORT']})
        # print("updated port")
    print(request.environ['REMOTE_PORT'])
    return jsonify({'ip': request.remote_addr}), 200

@app.route('/getallnodes', methods=['POST'])
def allnodes():
    print(ip_data)
    print(ip_port)
    return jsonify({'ip': request.remote_addr}), 200

@app.route('/getdata', methods=['POST'])
def getdata():
    filenames = next(walk("data/"), (None, None, []))[2]  # [] if no file
    interest_packet=request.data.decode('UTF-8')
    print("Interest packet = ",interest_packet)
    if interest_packet in filenames:
        print("Found in local")
        f = open("data/"+interest_packet, 'r')
        interest_data = f.read()
        f.close()
        return interest_data
    print("not found in local")
    for key, value in ip_data.items():
        if interest_packet in value.split(','):
            ip_withdata=key
            # print(ip_withdata)
            data_url = str(ip_withdata)+":33696/getdata"
            payload = interest_packet
            headers = {
            'Content-Type': 'text/plain'
            }
            try:
                response = requests.post(data_url, headers=headers, data=payload, timeout=0.5)
                print(response.text)
            except:
                print("Error, the Node is not up: ",data_url)
            return response.text
    print("Not Found")
    return 404

if __name__ == '__main__':
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=syncwithnodes, trigger="interval", seconds=20)
    # Shut down the scheduler when exiting the app
    atexit.register(lambda: scheduler.shutdown())
    # syncwithnodes()
    scheduler.start()
    app.run(host="localhost",port=33696)



