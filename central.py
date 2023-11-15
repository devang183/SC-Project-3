from flask import Flask, jsonify, request, Response
import requests
from collections import defaultdict
import socket
import atexit, json
from apscheduler.schedulers.background import BackgroundScheduler
#----------Sambit----------------
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
from rbac import is_admin, users
import tpm as ss
#---------------------------------
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


#-----------------RBAC (Sambit)----------------
app.config['JWT_SECRET_KEY'] = 'your_secret_key'
jwt = JWTManager(app)
storage = ss.SecureStorage()
#----------------------------------------

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
    scheduler.add_job(func=check_alive, trigger="interval", seconds=5)
    # Shut down the scheduler when exiting the app
    atexit.register(lambda: scheduler.shutdown())
    # syncwithnodes()
    scheduler.start()
    app.run(host="localhost", port=33700)