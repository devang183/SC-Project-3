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
import urllib3
import ipaddress
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

#-----Sambit---------------
import encryptionCompression as ec
import base64
from base64 import b64decode
import tpm as ss
from flask import send_file
#--------------------------

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
aes_key = ec.load_aes_key_from_file('aes_key.bin')
central_url =  "https://rasp-028.berry.scss.tcd.ie:33700"
# central_url="https://10.35.70.28:33700"

# central_url= "https://localhost:33700"
headers = {
            'Content-Type': 'application/json'
            }

def syncwithnodes():
    # print("chalu hogaya bhai")
    # print(filenames)
    # print(type(filenames))
    # filenames = next(walk("data/"), (None, None, []))[2]  # [] if no file
    # filenames = ','.join(filenames)
    base_url = "https://"+hostname[:-2]+"{}"+".berry.scss.tcd.ie:33696/register"
    data_payload = {
    "node_name":args.name,
    "node_address": IPAddr,
    "device_names": ','.join(list(registered_devices)),
    "sensor_name":','.join(list(registered_sensors)),
    "sensor_port":','.join(list(registered_sensors.values()))}
    json_payload = json.dumps(data_payload)
    # print(data_payload)
    #for JSON data
    json_data_bytes = json_payload.encode('utf-8')
    encrypted_data = ec.encrypt_message(json_data_bytes, aes_key)
    # print("Encrypted data:", encrypted_data)
    try:
        # print(central_url+"/centralregistry")
        response = requests.post(central_url+"/centralregistry", headers=headers, data=encrypted_data, timeout=1, verify=False)

        return response.status_code
    except:
        print("central server down, distributed mode enabled")
        broadcast_address = "10.35.70.255"
        # print(broadcast_address)
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        server_socket.sendto(encrypted_data, (broadcast_address, 33650))
        server_socket.close()
        return True

def discover_services(port=33650):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    client_socket.bind(('0.0.0.0', port))
    # client_socket.settimeout(10)
    while True:
        try:
            # print("Listening for distributed services")
            data, addr = client_socket.recvfrom(1024)
        except socket.timeout:
            print("Socket Timeout")
            # return False
        try:
            data = ec.decrypt_message(data, aes_key)
            # print("Decrypted data:", data)
            data = json.loads(data.decode('utf-8'))
            # print(f"Discovered service: {data}")
            if 'node_name' in data and (data['node_name']!=args.name):
                dis_registered_nodes[data['node_name']] = "https://rasp-0"+str(data['node_address'])[-2:]+".berry.scss.tcd.ie"
                dis_registered_devices[data['node_name']] = data['device_names'].split(',')
                dis_registered_sensors[data['node_name']] = data['sensor_name'].split(',')
                dis_registered_sensors_ports[data['node_name']] = data['sensor_port'].split(',')
                # dis_registration_timestamps[data['node_name']] = time.time()
                print("Distributed Nodes: ",dis_registered_nodes)
                print("Distributed Devices: ",dis_registered_devices)
                print("Distributed Sensors: ",dis_registered_sensors)
                print("Distributed Sensor Ports: ",dis_registered_sensors_ports)
                # return True
            else:
                pass
                # print("Received a broadcast, but it lacks required fields.")
                # return False
        except:
            print("Distributed Down")
            # return False


@app.route('/checkalive', methods=['GET'])
def check_alive():
    # print(hostname, IPAddr)
    return jsonify({'message': '{} is alive!'.format("https://rasp-0"+str(IPAddr)[-2:]+".berry.scss.tcd.ie")}), 200

def hit_alive():
    for node_name, node_add in dis_registered_nodes.copy().items():
        # print(f"Node Address: {node_address}")
        try:
            response = requests.get(node_add+":33696/checkalive", timeout=1, verify=False)
            response.raise_for_status()  # Raises an HTTPError for bad responses (4xx and 5xx)
        except requests.exceptions.RequestException as e:
            dis_registered_nodes.pop(node_name)
            dis_registered_devices.pop(node_name)
            dis_registered_sensors.pop(node_name)
            dis_registered_sensors_ports.pop(node_name)
    
    for sensor_name, sensor_port in registered_sensors.copy().items():
        # print(sensor_name, sensor_port)
        try:
            response = requests.get("https://localhost:"+sensor_port+"/checkalive", timeout=1, verify=False)
            response.raise_for_status()  # Raises an HTTPError for bad responses (4xx and 5xx)
            # print(response.json())
        except requests.exceptions.RequestException as e:
            registered_sensors.pop(sensor_name)

def cleanup_devices():
    current_time = time.time()
    # Iterate over devices and remove those not updated in the last 5 seconds
    devices_to_remove = [device for device, timestamp in device_registration_timestamps.copy().items() if current_time - timestamp > 8]
    for device in devices_to_remove:
        del registered_devices[device]
        del device_registration_timestamps[device]
    # print("Devices Removed: ", devices_to_remove)
    # print(registered_devices)
    return ("Cleaned: ",devices_to_remove)

@app.route('/register', methods=['POST'])
def register_node():
    data = request.data
    data = ec.decrypt_message(data, aes_key)
    # print("Decrypted data:", data)
    decoded_data = data.decode('utf-8')
    data = json.loads(decoded_data)
    if 'node_name' in data and data['node_name']==args.name:
        return jsonify({'message': 'Pls dont register yourself'}), 200
    # print(data)
    if 'node_name' in data and (data['node_name']!=args.name):
        dis_registered_nodes[data['node_name']] = "https://rasp-0"+str(data['node_address'])[-2:]+".berry.scss.tcd.ie"
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
            registered_nodes[node_name] = "https://rasp-0"+str(node_add)[-2:]+".berry.scss.tcd.ie"
            # registered_nodes["https://rasp-0"+str(node_address)[-2:]+".berry.scss.tcd.ie"] = node_data
            # print(f"Node registered: {node_name} , ","https://rasp-0"+str(node_add)[-2:]+".berry.scss.tcd.ie")
            # print(registered_nodes)
            return jsonify({'message': 'Registration successful'}), 200
        elif 'device_name' in data:
            # print(data)
            device_name = data['device_name']
            interest = data['interest']
            # registered_nodes["https://rasp-0"+str(node_address)[-2:]+".berry.scss.tcd.ie"] = node_data
            registered_devices[device_name] = interest
            device_registration_timestamps[device_name] = time.time()
            # print(f"Devuce registered: {device_name} , ","https://rasp-0"+str(node_address)[-2:]+".berry.scss.tcd.ie")
            # print("Device Registered: ", device_name)
            # print(registered_devices)
            return jsonify({'message': 'Registration successful'}), 200
        else:
            print("incorrect json in registration")
            return jsonify({'message': 'Incorrect Json'}), 404


@app.route('/getallnodes', methods=['POST'])
def allnodes():
    print(registered_nodes)
    # print(ip_port)
    return jsonify({'ip': request.remote_addr}), 200


#-----------------------SECURE STORAGE(TPM implementation) Sambit--------------------------

@app.route('/store_secured_peers', methods=['POST'])
def store_secured_peers():
    storage.save_data(request.remote_addr)
    return jsonify({'ip': request.remote_addr}), 200

@app.route('/read_secure_storage', methods=['GET'])
def read_secure_storage():
    retrieved_data = storage.retrieve_data()
    print("Retrieved Data:", retrieved_data)
    return jsonify({retrieved_data}), 200


#-----------------------ENCRYPTION AND COMPRESSION (Sambit)--------------------------
@app.route('/share_key', methods=['POST'])
def share_private_key_function():

    #Only the selected IPs will be able to download the file

    try:
        return send_file('aes_key.bin', as_attachment=True)
    except FileNotFoundError:
        pass  # Do nothing here or handle the exception

    # If the loop completes without returning, handle the case when the file is not found
    return "File not found", 404


@app.route('/broadcast', methods=['POST'])
def BroadCastTextData():
    print("Broadcasting")
    csv_data = request.data.decode('utf-8')
    loaded_aes_key = ec.load_aes_key_from_file('aes_key.bin') 
    compressed_data = ec.compress_text(csv_data) 
    encrypted_data = ec.encrypt_message(compressed_data, loaded_aes_key)
    encoded_data = base64.b64encode(encrypted_data).decode('utf-8')
    with open('encrypted_data.txt', 'wb') as file:
        file.write(encoded_data.encode('utf-8'))
    return jsonify({"data": encoded_data})

@app.route('/read_data', methods=['POST'])
def read_data():
    data = request.json.get('data')
    print("Encrypted data:", data)
    loaded_aes_key = ec.load_aes_key_from_file('aes_key.bin')
    decrypted_message = ec.decrypt_message(b64decode(data), loaded_aes_key)
    decompressed_text = ec.decompress_text(decrypted_message)
    print("Decrypted data:", decompressed_text)
    return decompressed_text
#--------------------------------------------

@app.route('/getsensordata', methods=['POST'])
def getsensordata():
    data=request.get_json()
    # print(data)
    interest_sensor=data['sensor_val']
    headers_csv = {
            'Content-Type': 'text/csv',
            'Content-Disposition': 'attachment; filename={}.csv'.format(interest_sensor)
            }
    # print("Interest sensor = ",interest_sensor)
    if interest_sensor in registered_sensors:
        sensor_port = registered_sensors[interest_sensor]
        #change the URL for PI
        sensor_url = "https://localhost:"+sensor_port+"/sensor_data/"+data['duration']
        try:
            # print(sensor_url)
            response = requests.get(sensor_url, timeout=1, verify=False)
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
            payload = json.dumps(payload)
            # print(payload)
            response = requests.post(central_url+"/finddata", headers=headers, data=payload, timeout=5, verify=False)
            # print(response.json())
            json_resp = response.json()
            response.raise_for_status()
            response = requests.post(json_resp["data_available"], headers=headers, data=payload, timeout=5, verify=False)
            return Response(response.text, headers=headers_csv)
        except:
            print("Central down, Trying distributed")
            #---------------------------------------------communicate with central and distributed
        try:
            # print("trying distributed")
            for key, value in dis_registered_sensors.copy().items():
                if interest_sensor in value:
                    payload = {"sensor_val":interest_sensor, "duration":data['duration']}
                    payload = json.dumps(payload)
                    ip_withdata=dis_registered_nodes[key]
                    # print(ip_withdata)
                    data_url = str(ip_withdata)+":33696/getsensordata"
                    # print(data_url)
                    response = requests.post(data_url, headers=headers, data=payload, timeout=5, verify=False)
                    response.raise_for_status()
                    # print("Response from distributed ",response.text)
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
        response = requests.post(central_url+"/centralregistry", headers=headers, data=interest_payload, timeout=1, verify=False)
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
                    response = requests.post(data_url, headers=headers, data=payload, timeout=5, verify=False)
                    print(response)
                except:
                    print("Error, the Node is not up: ",data_url)
                return response.json()
        print("Not Found")
        return 404

if __name__ == '__main__':
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=syncwithnodes, trigger="interval", seconds=5)
    scheduler.add_job(func=hit_alive, trigger="interval", seconds=10)
    scheduler.add_job(func=cleanup_devices, trigger="interval", seconds=10)
    scheduler.add_job(func=discover_services, trigger="interval", seconds=10, max_instances=1, replace_existing=True)
    
    #------------------Sambit's changes------------------
    storage = ss.SecureStorage()
    #--------------------------
    # Shut down the scheduler when exiting the app
    atexit.register(lambda: scheduler.shutdown())
    # syncwithnodes()
    scheduler.start()
    app.run(host="0.0.0.0",port=33696, ssl_context='adhoc')


