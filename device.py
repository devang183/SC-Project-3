import requests
from os import walk
import json
import argparse
import time
import socket
import atexit
from apscheduler.schedulers.background import BackgroundScheduler
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

import encryptionCompression as ec
aes_key = ec.load_aes_key_from_file('aes_key.bin')

hostname = socket.gethostname()
IPAddr = socket.gethostbyname(hostname)
# central_url= "httpss://localhost:33700/finddata"
node_address = "https://127.0.0.1:33696/register"
headers = {
            'Content-Type': 'application/json'
            }
node_sensor_url= "https://127.0.0.1:33696/getsensordata"

parser = argparse.ArgumentParser(description='Run device with the interest packet')
parser.add_argument('--interest', type=str, help='Query interest file')
parser.add_argument('--name', type=str, help='Name of the device')
parser.add_argument('--data', nargs='+', type=str, help='List of values')
parser.add_argument('--duration', type=str, help='List of values')

args = parser.parse_args()
sensor_data_req = args.data

def get_sensor_data():
    for data in sensor_data_req:
        data_payload = {"sensor_val": data, "duration": args.duration}
        data_payload = json.dumps(data_payload)
        print(data_payload)
        try:
            response = requests.post(node_sensor_url, headers=headers, data=data_payload, timeout=1, verify=False)
            response.raise_for_status()  # Raises an HTTPError for bad responses (4xx and 5xx)
            print(response.text)
        except requests.exceptions.RequestException as e:
            print("Unable to get sernsor data")
            return False

def broadcast_alive():
    json_payload = {"device_name": args.name, "interest": args.interest}
    data_payload = json.dumps(json_payload)
    json_data_bytes = data_payload.encode('utf-8')
    json_data_bytes = ec.encrypt_message(json_data_bytes, aes_key) 
    try:
        response = requests.post(node_address, headers=headers, data=json_data_bytes, timeout=1, verify=False)
        response.raise_for_status()  # Raises an HTTPError for bad responses (4xx and 5xx)
    except requests.exceptions.RequestException as e:
        print("Unable to register with server")

# def recv_data():
#     # base_url = "httpss://"+hostname[:-2]+"{}"+".berry.scss.tcd.ie:33696/registernodes"
#     interest_packet=args.interest
#     print("Interest packet = ",interest_packet)
#     interest_payload = {"interest_data": interest_packet}
#     interest_payload = json.dumps(interest_payload)
#     try:
#         response = requests.post(central_url, headers=headers, data=interest_payload, timeout=1)
#         print(response.json())
#         return response.json()
#     except:
#         print("Central server down, Distributed mode enabled")
#         # data_url ="httpss://rasp-0"+str(IPAddr)[-2:]+".berry.scss.tcd.ie:33696/getdata"
#         data_url ="httpss://localhost:33696/getdata"
#         response = requests.post(data_url, headers=headers, data=interest_payload, timeout=5)
#         print(response.json())

scheduler = BackgroundScheduler()
# scheduler.add_job(func=recv_data, trigger="interval", seconds=5)
scheduler.add_job(func=broadcast_alive, trigger="interval", seconds=5)
scheduler.add_job(func=get_sensor_data, trigger="interval", seconds=10)

# Shut down the scheduler when exiting the app
atexit.register(lambda: scheduler.shutdown())
# syncwithnodes()
scheduler.start()

try:
    while True:
        time.sleep(10)
        pass
except (KeyboardInterrupt, SystemExit):
    # Cleanly shut down the scheduler
    scheduler.shutdown()
    print("Script terminated.")
