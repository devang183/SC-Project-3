from flask import Flask, jsonify, request
import requests
from collections import defaultdict
import socket
import atexit
from apscheduler.schedulers.background import BackgroundScheduler

hostname = socket.gethostname()
IPAddr = socket.gethostbyname(hostname)

app = Flask(__name__)
# Dictionary to store information about registered nodes
registered_nodes = defaultdict(dict)

@app.route('/centralregistry', methods=['POST'])
def register_node():
    data = request.get_json()
    node_address = data['node_address']
    node_data = data['node_data']
    # Store registration information
    registered_nodes["http://rasp-0"+str(node_address)[-2:]+".berry.scss.tcd.ie"] = node_data
    print(f"Node registered: {node_address} , ","http://rasp-0"+str(node_address)[-2:]+".berry.scss.tcd.ie")
    print(registered_nodes)
    return jsonify({'message': 'Registration successful'}), 200

def check_alive():
    for node_address, node_data in registered_nodes.copy().items():
        # print(f"Node Address: {node_address}")
        try:
            response = requests.get(node_address+"/checkalive")
            response.raise_for_status()  # Raises an HTTPError for bad responses (4xx and 5xx)
            print(f"Success! Status Code: {response.status_code}")
            print(response.json())  # Assuming the response contains JSON data
        except requests.exceptions.RequestException as e:
            removed_value = registered_nodes.pop(node_address)
            print("Removed Node: {} with data: {}".format(node_address,removed_value))
            print(f"Error: {e}")

@app.route('/finddata', methods=['POST'])
def find_data():
    data=request.get_json()
    interest_packet=data['interest_data']
    print("Interest packet = ",interest_packet)
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
                response = requests.post(data_url, headers=headers, data=payload, timeout=0.5)
                print(response.text)
                response = response
            except:
                print("Error, the Node is not up: ",data_url)
            # return response.text
            return jsonify({'data': respons}), 200

    return 404

if __name__ == '__main__':
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=check_alive, trigger="interval", seconds=5)
    # Shut down the scheduler when exiting the app
    atexit.register(lambda: scheduler.shutdown())
    # syncwithnodes()
    scheduler.start()
    app.run(host="localhost", port=33697)