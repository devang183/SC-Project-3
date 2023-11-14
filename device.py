from flask import Flask, jsonify, request
import requests
from os import walk
import json
import argparse
import socket
import atexit
from apscheduler.schedulers.background import BackgroundScheduler
hostname = socket.gethostname()
IPAddr = socket.gethostbyname(hostname)
central_url= "http://localhost:33700/finddata"
headers = {
            'Content-Type': 'application/json'
            }
node_address = "localhost:33696/registerdevices"

parser = argparse.ArgumentParser(description='Run device with the interest packet')
parser.add_argument('--interest', type=str, help='Query interest file')
parser.add_argument('--name', type=str, help='Name of the device')
args = parser.parse_args()

def get_sensor_data():
    

def broadcast_alive():
    data_payload = {"interest_data": interest_packet}
    data_payload = json.dumps(data_payload)
    try:
        response = requests.post(node_address, timeout=1)
        response.raise_for_status()  # Raises an HTTPError for bad responses (4xx and 5xx)
        # print(f"Success! Status Code: {response.status_code}")
        # print(response.json())  # Assuming the response contains JSON data
    except requests.exceptions.RequestException as e:
        print("Unable to register with server")

def recv_data():
    # base_url = "http://"+hostname[:-2]+"{}"+".berry.scss.tcd.ie:33696/registernodes"
    interest_packet=args.interest
    print("Interest packet = ",interest_packet)
    interest_payload = {"interest_data": interest_packet}
    interest_payload = json.dumps(interest_payload)
    try:
        response = requests.post(central_url, headers=headers, data=interest_payload, timeout=1)
        print(response.json())
        return response.json()
    except:
        print("Central server down, Distributed mode enabled")
        # data_url ="http://rasp-0"+str(IPAddr)[-2:]+".berry.scss.tcd.ie:33696/getdata"
        data_url ="localhost:33696/getdata"
        response = requests.post(data_url, headers=headers, data=interest_payload, timeout=5)
        print(response.json())

scheduler = BackgroundScheduler()
scheduler.add_job(func=recv_data, trigger="interval", seconds=20)
# Shut down the scheduler when exiting the app
atexit.register(lambda: scheduler.shutdown())
# syncwithnodes()
scheduler.start()