import time
from flask import Flask, jsonify, request
import requests
from os import walk
import json
import argparse
import socket
import atexit
from apscheduler.schedulers.background import BackgroundScheduler
from statsmodels.tsa.holtwinters import ExponentialSmoothing

hostname = socket.gethostname()
IPAddr = socket.gethostbyname(hostname)
central_url = "http://localhost:33700/finddata"
headers = {'Content-Type': 'application/json'}
node_address = "localhost:33696/registerdevices"


parser = argparse.ArgumentParser(description='Run device with the interest packet')
parser.add_argument('--interest', type=str, help='Query interest file')
parser.add_argument('--name', type=str, help='Name of the device')
args = parser.parse_args()

# def get_sensor_data():

'''
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
'''

def recv_data():
    # base_url = "http://"+hostname[:-2]+"{}"+".berry.scss.tcd.ie:33696/registernodes"
    interest_packet = args.interest
    print("Interest packet = ", interest_packet)
    interest_payload = {"interest_data": interest_packet}
    interest_payload = json.dumps(interest_payload)
    try:
        response = requests.post(central_url, headers=headers, data=interest_payload, timeout=1)
        print(response.json())
        return response.json()
    except:
        print("Central server down, Distributed mode enabled")
        # data_url ="http://rasp-0"+str(IPAddr)[-2:]+".berry.scss.tcd.ie:33696/getdata"
        data_url = "localhost:33696/getdata"

        start_time = time.time()
        response = requests.post(data_url, headers=headers, data=interest_payload, timeout=5)
        end_time = time.time()
        check_congestion(start_time, end_time)

        print(response.json())


response_times = []
def check_congestion(start_time, end_time):
    response_time = (end_time - start_time) * 1000
    print(f"RTT: {response_time} ms")

    response_times.append(response_time)

    #ETS to predict the congestion one step ahead (good for seasonal variations if there are sudden spikes periodically)
    ets_model = ExponentialSmoothing(response_times, seasonal='add', seasonal_periods=24)
    ets_fit = ets_model.fit()
    forecast = ets_fit.forecast(steps=1)

    if forecast > 2000:  # MODIFY TO ADEQUATE VALUE!!!
        #Generate an alert
        print("Warning: Congestion predicted, actions taken")
        #Logging: Record the event in a log
        congestion_events(response_time)
        #Reduce the job frequency
        scheduler.modify_job('recv_data', trigger='interval', seconds=20)

        #Signal the sever that congestion is bad for further actions
        #signal_congestion_to_server()

    else:
        print("No congestion predicted")
        scheduler.modify_job('recv_data', trigger='interval', seconds=10)

def congestion_events(response_time):
    with open('congestion_log.txt', 'a') as log_file:
        log_file.write(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}, RTT: {response_time} ms\n")



'''
server_url = "http://localhost:33696/congestionstatus"
def signal_congestion_to_server():
    congestion_data = {
        'device_name': args.name,
        'congestion_status': 'congested',  # You can customize the status as needed
    }
    try:
        response = requests.post(server_url, headers={'Content-Type': 'application/json'}, json=congestion_data, timeout=1)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print("Error signaling congestion to server:", str(e))
'''
#Its on the server's side to check if it receives too many requests to detect a DDos attack following the warning (can also use ML)
#Its on the server's side to make further modification to ease congestion by decreasing the scheduler's job frequencies (for example)

scheduler = BackgroundScheduler()
scheduler.add_job(func=recv_data, trigger="interval", seconds=10)
# Shut down the scheduler when exiting the app
atexit.register(lambda: scheduler.shutdown())
# syncwithnodes()
scheduler.start()

