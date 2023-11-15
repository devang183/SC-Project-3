from flask import Flask, jsonify, request, Response
import requests
from collections import defaultdict
import socket
import atexit, json
from apscheduler.schedulers.background import BackgroundScheduler

hostname = socket.gethostname()
IPAddr = socket.gethostbyname(hostname)

headers = {
            'Content-Type': 'application/json'
            }

app = Flask(__name__)
# Dictionary to store information about registered nodes
registered_nodes = defaultdict(dict)
registered_devices = defaultdict(dict)
registered_sensors = defaultdict(dict)
registered_sensors_ports = defaultdict(dict)

@app.route('/centralregistry', methods=['POST'])
def register_node():
    # print(request)
    data = request.get_json()
    registered_nodes[data['node_name']] = data['node_address']
    registered_devices[data['node_name']] = data['device_names'].split(',')
    registered_sensors[data['node_name']] = data['sensor_name'].split(',')
    registered_sensors_ports[data['node_name']] = data['sensor_port'].split(',')
    # Store registration information
    #change for PI
    # registered_nodes["http://rasp-0"+str(node_address)[-2:]+".berry.scss.tcd.ie"] = node_data
    # registered_sensors[sensor_name] = sensor_port
    # print(f"Node registered: {node_address} , ","http://rasp-0"+str(node_address)[-2:]+".berry.scss.tcd.ie")
    print(registered_nodes)
    print(registered_devices)
    print(registered_sensors)
    print(registered_sensors_ports)
    return jsonify({'message': 'Registration successful'}), 200

def check_alive():
    for node_name, node_add in registered_nodes.copy().items():
        # print(f"Node Address: {node_address}")
        try:
            response = requests.get(node_add+"/checkalive", timeout=1)
            response.raise_for_status()  # Raises an HTTPError for bad responses (4xx and 5xx)
        except requests.exceptions.RequestException as e:
            registered_nodes.pop(node_name)
            registered_devices.pop(node_name)
            registered_sensors.pop(node_name)
            registered_sensors_ports.pop(node_name)

@app.route('/finddata', methods=['POST'])
def find_data():
    data=request.get_json()
    interest_sensor=data['sensor_val']
    print("Interest sensor = ",interest_sensor)
    headers_csv = {
            'Content-Type': 'text/csv',
            'Content-Disposition': 'attachment; filename={}.csv'.format(interest_sensor)
            }
    payload = {"sensor_val":interest_sensor, "duration":data['duration']}
    for key, value in registered_sensors.copy().values():
        if interest_sensor in value:
            ip_withdata=registered_nodes[key]
            # print(ip_withdata)
            data_url = str(ip_withdata)+":33696/getsensordata"
            response = requests.post(data_url, headers=headers, data=payload, timeout=5)
            response.raise_for_status()
            # print("Response from server ",response.text)
            return Response(response.text, headers=headers_csv)
    return 404

if __name__ == '__main__':
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=check_alive, trigger="interval", seconds=5)
    # Shut down the scheduler when exiting the app
    atexit.register(lambda: scheduler.shutdown())
    # syncwithnodes()
    scheduler.start()
    app.run(host="localhost", port=33700)