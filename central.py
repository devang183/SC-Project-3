from flask import Flask, jsonify, request, Response
import requests
from collections import defaultdict
import socket
import atexit, json
from apscheduler.schedulers.background import BackgroundScheduler
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

#----------Sambit----------------
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
from rbac import is_admin, users
import tpm as ss
import encryptionCompression as ec
#---------------------------------
hostname = socket.gethostname()
IPAddr = socket.gethostbyname(hostname)

headers = {
            'Content-Type': 'application/json'
            }
aes_key = ec.load_aes_key_from_file('aes_key.bin')
app = Flask(__name__)
# Dictionary to store information about registered nodes
registered_nodes = defaultdict(dict)
registered_devices = defaultdict(dict)
registered_sensors = defaultdict(dict)
registered_sensors_ports = defaultdict(dict)

#-----------------RBAC (Sambit)----------------
app.config['JWT_SECRET_KEY'] = 'your_secret_key'
jwt = JWTManager(app)
storage = ss.SecureStorage()
#----------------------------------------

@app.route('/centralregistry', methods=['POST'])
def register_node():
    # print(request)
    data = request.data
    data = ec.decrypt_message(data, aes_key)
    # print("Decrypted data:", data)
    decoded_data = data.decode('utf-8')
    data = json.loads(decoded_data)
    registered_nodes[data['node_name']] = "https://rasp-0"+str(data['node_address'])[-2:]+".berry.scss.tcd.ie"
    registered_devices[data['node_name']] = data['device_names'].split(',')
    registered_sensors[data['node_name']] = data['sensor_name'].split(',')
    registered_sensors_ports[data['node_name']] = data['sensor_port'].split(',')
    # Store registration information
    #change for PI
    # registered_nodes["https://rasp-0"+str(node_address)[-2:]+".berry.scss.tcd.ie"] = node_data
    # registered_sensors[sensor_name] = sensor_port
    # print(f"Node registered: {node_address} , ","https://rasp-0"+str(node_address)[-2:]+".berry.scss.tcd.ie")
    return jsonify({'message': 'Registration successful'}), 200

def check_alive():
    for node_name, node_add in registered_nodes.copy().items():
        # print(registered_nodes)
        try:
            # print(node_name)
            # print(node_add+"/checkalive")
            response = requests.get(node_add+"/checkalive", timeout=5, verify=False)
            response.raise_for_status()  # Raises an HTTPError for bad responses (4xx and 5xx)
        except requests.exceptions.RequestException as e:
            registered_nodes.pop(node_name)
            registered_devices.pop(node_name)
            registered_sensors.pop(node_name)
            registered_sensors_ports.pop(node_name)

def print_list():
    print("Registered Nodes: ",registered_nodes)
    print("Registered Devives: ",registered_devices)
    print("Registered Sensors: ",registered_sensors)
    print("Registered Sensor Ports: ",registered_sensors_ports)

@app.route('/finddata', methods=['POST'])
def find_data():
    data=request.get_json()
    interest_sensor=data['sensor_val']
    # print("Interest sensor = ",interest_sensor)
    headers_csv = {
            'Content-Type': 'text/csv',
            'Content-Disposition': 'attachment; filename={}.csv'.format(interest_sensor)
            }
    payload = {"sensor_val":interest_sensor, "duration":data['duration']}
    payload = json.dumps(payload)
    for key, value in registered_sensors.copy().items():
        if interest_sensor in value:
            ip_withdata=registered_nodes[key]
            # print(ip_withdata)
            data_url = str(ip_withdata)+":33696/getsensordata"
            # print(data_url)
            return_json = {"data_available": data_url}
            return_json = json.dumps(return_json)
            # response = requests.post(data_url, headers=headers, data=payload, timeout=5, verify=False)
            # response.raise_for_status()
            # print("Response from server ",response.text)
            return Response(return_json, headers=headers)
    return 404
#--------------------RBAC (Sambit)--------------------
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if username in users and users[username]['password'] == password:
        access_token = create_access_token(identity={'username': username, 'roles': users[username]['roles']})
        return jsonify(access_token=access_token), 200
    else:
        return jsonify({"message": "Invalid credentials"}), 401

@app.route('/read_secure_storage', methods=['GET'])
@jwt_required()
def read_secure_storage():
    current_user = get_jwt_identity()
    # Check if the user has the 'admin' role using the imported RBAC function
    if is_admin(current_user.get('username', '')):
        retrieved_data = storage.retrieve_data()
        print("Retrieved Data:", retrieved_data)
        #return jsonify({retrieved_data}), 200
        return jsonify({"secure storage data": f"{retrieved_data}"}), 200
    else:
        return jsonify({"message": "Access denied"}), 403
#--------------------RBAC----------------------------
if __name__ == '__main__':
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=check_alive, trigger="interval", seconds=10)
    scheduler.add_job(func=print_list, trigger="interval", seconds=10)
    # Shut down the scheduler when exiting the app
    atexit.register(lambda: scheduler.shutdown())
    # syncwithnodes()
    scheduler.start()
    app.run(host="0.0.0.0", port=33700, ssl_context='adhoc')