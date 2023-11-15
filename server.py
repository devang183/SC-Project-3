from flask import Flask, jsonify, request, Response
import requests
import time
import atexit
from apscheduler.schedulers.background import BackgroundScheduler
from os import walk
from collections import defaultdict
import socket
import json
import argparse
parser = argparse.ArgumentParser(description='Run network')
parser.add_argument('--name', type=str, help='Name of the node')
args = parser.parse_args()

hostname = socket.gethostname()
IPAddr = socket.gethostbyname(hostname)
registered_nodes = defaultdict(dict)
registered_devices = defaultdict(dict)
registered_sensors = defaultdict(dict)
device_registration_timestamps = defaultdict(dict)

dis_registered_nodes = defaultdict(dict)
dis_registered_devices = defaultdict(dict)
dis_registered_sensors = defaultdict(dict)
dis_registered_sensors_ports = defaultdict(dict)
dis_registration_timestamps = defaultdict(dict)

app = Flask(__name__)

# central_url =  "http://rasp-028.berry.scss.tcd.ie:33700/centralregistry"
central_url= "http://localhost:33700"
headers = {
            'Content-Type': 'application/json'
            }

def syncwithnodes():
    # print("chalu hogaya bhai")
    # print(filenames)
    # print(type(filenames))
    # filenames = next(walk("data/"), (None, None, []))[2]  # [] if no file
    # filenames = ','.join(filenames)
    base_url = "http://"+hostname[:-2]+"{}"+".berry.scss.tcd.ie:33696/register"
    data_payload = {
    "node_name":args.name,
    "node_address": IPAddr,
    "device_names": ','.join(list(registered_devices)),
    "sensor_name":','.join(list(registered_sensors)),
    "sensor_port":','.join(list(registered_sensors.values()))}
    json_payload = json.dumps(data_payload)
    # print(data_payload)
    try:
        response = requests.post(central_url+"/centralregistry", headers=headers, data=json_payload, timeout=1)
        return response.status_code
    except:
        print("central server down, distributed mode enabled")
        for i in range(1, 50): # ip range
            try:
                # print("trying ip: ",base_url.format(i))
                response = requests.post(base_url.format(i), headers=headers, data=data_payload, timeout=0.5)
            except:
                n = 0
        # print(ip_data)
        # print(ip_port)
        return True

@app.route('/checkalive', methods=['GET'])
def check_alive():
    # print(hostname, IPAddr)
    return jsonify({'message': '{} is alive!'.format("http://rasp-0"+str(IPAddr)[-2:]+".berry.scss.tcd.ie")}), 200

def hit_alive():
    for node_name, node_add in registered_nodes.copy().items():
        # print(f"Node Address: {node_address}")
        try:
            response = requests.get(node_add+"/checkalive", timeout=1)
            response.raise_for_status()  # Raises an HTTPError for bad responses (4xx and 5xx)
        except requests.exceptions.RequestException as e:
            removed_value = registered_nodes.pop(node_name)
    
    for sensor_name, sensor_port in registered_sensors.copy().items():
        # print(sensor_name, sensor_port)
        try:
            response = requests.get("http://localhost:"+sensor_port+"/checkalive", timeout=1)
            response.raise_for_status()  # Raises an HTTPError for bad responses (4xx and 5xx)
            # print(response.json())
        except requests.exceptions.RequestException as e:
            removed_value = registered_sensors.pop(sensor_name)

def cleanup_devices():
    current_time = time.time()
    # Iterate over devices and remove those not updated in the last 5 seconds
    devices_to_remove = [device for device, timestamp in device_registration_timestamps.copy().items() if current_time - timestamp > 8]
    dis_to_remove = [node for node, timestamp in dis_registration_timestamps.copy().items() if current_time - timestamp > 8]
    for node in dis_to_remove:
        del dis_registered_nodes[node]
        del dis_registered_devices[node]
        del dis_registered_sensors[node]
        del dis_registered_sensors_ports[node]
        del device_registration_timestamps[node]
    for device in devices_to_remove:
        del registered_devices[device]
        del device_registration_timestamps[device]
    # print("Devices Removed: ", devices_to_remove)
    # print(registered_devices)
    return ("Cleaned: ",devices_to_remove)

@app.route('/register', methods=['POST'])
def register_node():
    data = request.get_json()
    # print(data)
    if 'node_name' in data and (data['node_name']!=args.name):
        dis_registered_nodes[data['node_name']] = data['node_address']
        dis_registered_devices[data['node_name']] = data['device_names'].split(',')
        dis_registered_sensors[data['node_name']] = data['sensor_name'].split(',')
        dis_registered_sensors_ports[data['node_name']] = data['sensor_port'].split(',')
        dis_registration_timestamps[data['node_name']] = time.time()
        return jsonify({'message': 'Distributed Node Registration successful'}), 200
    else:
        if 'sensor_name' in data:
            sensor_name = data['sensor_name']
            sensor_port = data['port']
            registered_sensors[sensor_name] = sensor_port
            # print(f"Sensor registered: {sensor_name} , ",f"with port: {sensor_port}")
            # print(registered_sensors)   
            return jsonify({'message': 'Device Registration successful'}), 200
        elif 'node_address' in data:
            node_name = data['node_name']
            node_add = data['node_add']
            registered_nodes[node_name] = "http://rasp-0"+str(node_add)[-2:]+".berry.scss.tcd.ie"
            # registered_nodes["http://rasp-0"+str(node_address)[-2:]+".berry.scss.tcd.ie"] = node_data
            print(f"Node registered: {node_name} , ","http://rasp-0"+str(node_add)[-2:]+".berry.scss.tcd.ie")
            print(registered_nodes)
            return jsonify({'message': 'Registration successful'}), 200
        elif 'device_name' in data:
            print(data)
            device_name = data['device_name']
            interest = data['interest']
            # registered_nodes["http://rasp-0"+str(node_address)[-2:]+".berry.scss.tcd.ie"] = node_data
            registered_devices[device_name] = interest
            device_registration_timestamps[device_name] = time.time()
            # print(f"Devuce registered: {device_name} , ","http://rasp-0"+str(node_address)[-2:]+".berry.scss.tcd.ie")
            print("Device Registered: ", device_name)
            print(registered_devices)
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
    headers_csv = {
            'Content-Type': 'text/csv',
            'Content-Disposition': 'attachment; filename={}.csv'.format(interest_sensor)
            }
    # print("Interest sensor = ",interest_sensor)
    if interest_sensor in registered_sensors:
        sensor_port = registered_sensors[interest_sensor]
        #change the URL for PI
        sensor_url = "http://localhost:"+sensor_port+"/sensor_data/"+data['duration']
        try:
            print(sensor_url)
            response = requests.get(sensor_url, timeout=1)
            response.raise_for_status()
            # print(response.text)
            return Response(response.text, headers=headers_csv)
        except:
            #if local server down, try central and distributed
            print("Incorrect JSON")
            return jsonify({'message': 'Incorrect Json'}), 404
    else:#if its not available locally, try central and distributed
        print(registered_sensors)
        try:
            print("trying central")
            headers = {
                    'Content-Type': 'application/json'
                    }
            payload = {"sensor_val":interest_sensor, "duration":data['duration']}
            response = requests.post(central_url+"/finddata", headers=headers, data=payload, timeout=5)
            response.raise_for_status()
            print(response.text)
            return Response(response.text, headers=headers_csv)
        except:
            print("Central down, Trying distributed")
            #---------------------------------------------communicate with central and distributed
        try:
            print("trying distributed")
            for key, value in dis_registered_sensors.copy().values():
                if interest_sensor in value:
                    payload = {"sensor_val":interest_sensor, "duration":data['duration']}
                    ip_withdata=dis_registered_nodes[key]
                    # print(ip_withdata)
                    data_url = str(ip_withdata)+":33696/getsensordata"
                    response = requests.post(data_url, headers=headers, data=payload, timeout=5)
                    response.raise_for_status()
                    print("Response from distributed ",response.text)
                    return Response(response.text, headers=headers_csv)
        except:
            print("not available in distributed")
        return jsonify({'message': 'Incorrect Json/Not available'}), 404

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
        response = requests.post(central_url+"/centralregistry", headers=headers, data=interest_payload, timeout=1)
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
    scheduler.add_job(func=syncwithnodes, trigger="interval", seconds=5)
    scheduler.add_job(func=hit_alive, trigger="interval", seconds=5)
    scheduler.add_job(func=cleanup_devices, trigger="interval", seconds=5)
    # Shut down the scheduler when exiting the app
    atexit.register(lambda: scheduler.shutdown())
    # syncwithnodes()
    scheduler.start()
    app.run(host="0.0.0.0",port=33696)



