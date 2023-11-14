from flask import Flask, jsonify, request
import requests
import time
import atexit
from apscheduler.schedulers.background import BackgroundScheduler
from os import walk
from collections import defaultdict
import socket
import json
hostname = socket.gethostname()
IPAddr = socket.gethostbyname(hostname)
registered_nodes = defaultdict(dict)
registered_devices = defaultdict(dict)
registered_sensors = defaultdict(dict)
app = Flask(__name__)
ip_data={}
ip_port={}
code=0
# central_url =  "http://rasp-028.berry.scss.tcd.ie:33700/centralregistry"
central_url= "http://localhost:33700/centralregistry"
headers = {
            'Content-Type': 'application/json'
            }

def syncwithnodes():
    # print("chalu hogaya bhai")
    # print(filenames)
    # print(type(filenames))
    filenames = next(walk("data/"), (None, None, []))[2]  # [] if no file
    filenames = ','.join(filenames)
    base_url = "http://"+hostname[:-2]+"{}"+".berry.scss.tcd.ie:33696/register"
    data_payload = {
    "node_address": IPAddr,    
    "node_data": filenames}
    json_payload = json.dumps(data_payload)
    # print(data_payload)
    try:
        response = requests.post(central_url, headers=headers, data=json_payload, timeout=1)
        return response.status_code
    except:
        print("central server down, distributed mode enabled")
        for i in range(1, 50): # ip range
            try:
                # print("trying ip: ",base_url.format(i))
                response = requests.post(base_url.format(i), headers=headers, data=data_payload, timeout=0.5)
            except:
                n = 0
        print(ip_data)
        # print(ip_port)
        return True

@app.route('/checkalive', methods=['GET'])
def check_alive():
    # print(hostname, IPAddr)
    return jsonify({'message': '{} is alive!'.format("http://rasp-0"+str(IPAddr)[-2:]+".berry.scss.tcd.ie")}), 200

def hit_alive():
    for node_address, node_data in registered_nodes.copy().items():
        # print(f"Node Address: {node_address}")
        try:
            response = requests.get(node_address+"/checkalive", timeout=1)
            response.raise_for_status()  # Raises an HTTPError for bad responses (4xx and 5xx)
        except requests.exceptions.RequestException as e:
            removed_value = registered_nodes.pop(node_address)
    
    for sensor_add, sensor_data in registered_sensors.copy().items():
        # print(f"Node Address: {node_address}")
        try:
            response = requests.get(sensor_add+"/checkalive", timeout=1)
            response.raise_for_status()  # Raises an HTTPError for bad responses (4xx and 5xx)
        except requests.exceptions.RequestException as e:
            removed_value = registered_sensors.pop(sensor_add)

@app.route('/register', methods=['POST'])
def register_node():
    data = request.get_json()
    if 'sensor_data' in data:
        sensor_name = data['sensor_data']
        sensor_port = data['port']
        # Store registration information
        registered_sensors[sensor_name] = sensor_port
        print(f"Sensor registered: {sensor_name} , ",f"with port: {sensor_port}")
        print(registered_sensors)
        return jsonify({'message': 'Device Registration successful'}), 200
    elif 'node_address' in data:
        node_address = data['node_address']
        node_data = data['node_data']
        # Store registration information
        registered_nodes["http://rasp-0"+str(node_address)[-2:]+".berry.scss.tcd.ie"] = node_data
        print(f"Node registered: {node_address} , ","http://rasp-0"+str(node_address)[-2:]+".berry.scss.tcd.ie")
        print(registered_nodes)
        return jsonify({'message': 'Registration successful'}), 200
    else:
        print("incorrect json in registration")
        return jsonify({'message': 'Incorrect Json'}), 404

@app.route('/getallnodes', methods=['POST'])
def allnodes():
    print(registered_nodes)
    # print(ip_port)
    return jsonify({'ip': request.remote_addr}), 200

@app.route('/getsensordata', methods=['POST'])
def getsensordata():
    data=request.get_json()
    interest_sensor=data['sensor_val']
    print("Interest sensor = ",interest_sensor)
    if interest_sensor in registered_sensors:
        sensor_port = registered_sensors[interest_sensor]
    else:
        return jsonify({'message': 'Incorrect Json'}), 404
    sensor_url = "localhost:"+sensor_port+"sensor_data/"+data['duration']
    try:
        response = requests.get(sensor_url, timeout=1)
        return response
    except:
        print("{} Sensor down",interest_sensor)

@app.route('/getdata', methods=['POST'])
def getdata():
    filenames = next(walk("data/"), (None, None, []))[2]  # [] if no file
    # interest_packet=request.data.decode('UTF-8')
    data=request.get_json()
    interest_packet=data['interest_data']
    print("Interest packet = ",interest_packet)
    interest_payload = {"interest_data": interest_packet}
    interest_payload = json.dumps(interest_payload)
    try:
        response = requests.post(central_url, headers=headers, data=interest_payload, timeout=1)
        return response.json()
    except:
        print("Distributed mode being used")
        if interest_packet in filenames:
            print("Found in local")
            f = open("data/"+interest_packet, 'r')
            interest_data = f.read()
            f.close()
            return jsonify({'data': interest_data}), 200
        print("not found in local")
        # for key, value in ip_data.items():
        for key, value in registered_nodes.copy().items():
            if interest_packet in value.split(','):
                ip_withdata=key
                # print(ip_withdata)
                data_url = str(ip_withdata)+":33696/getdata"
                payload = {"interest_data": interest_packet}
                headers = {
                'Content-Type': 'application/json'
                }
                try:
                    response = requests.post(data_url, headers=headers, data=payload, timeout=5)
                    print(response)
                except:
                    print("Error, the Node is not up: ",data_url)
                return response.json()
        print("Not Found")
        return 404

if __name__ == '__main__':
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=syncwithnodes, trigger="interval", seconds=20)
    scheduler.add_job(func=hit_alive, trigger="interval", seconds=30)
    # Shut down the scheduler when exiting the app
    atexit.register(lambda: scheduler.shutdown())
    # syncwithnodes()
    scheduler.start()
    app.run(host="0.0.0.0",port=33696)



