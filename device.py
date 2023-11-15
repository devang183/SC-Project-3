import requests
from os import walk
import json
import argparse
import socket
import atexit
from apscheduler.schedulers.background import BackgroundScheduler
hostname = socket.gethostname()
IPAddr = socket.gethostbyname(hostname)
# central_url= "http://localhost:33700/finddata"
headers = {
            'Content-Type': 'application/json'
            }
node_address = "http://127.0.0.1:33696/register"
node_sensor_url= "http://127.0.0.1:33696/getsensordata"

parser = argparse.ArgumentParser(description='Run device with the interest packet')
parser.add_argument('--interest', type=str, help='Query interest file')
parser.add_argument('--name', type=str, help='Name of the device')
parser.add_argument('--data', nargs='+', type=str, help='List of values')
parser.add_argument('--duration', type=str, help='List of values')

args = parser.parse_args()
sensor_data_req = args.data

def get_sensor_data():
    for data in sensor_data_req:
        data_payload = {"sensor_val":data , "duration":args.duration}
        data_payload = json.dumps(data_payload)
        try:
            response = requests.post(node_sensor_url,headers=headers, data=data_payload, timeout=1)
            response.raise_for_status()  # Raises an HTTPError for bad responses (4xx and 5xx)
            print(response.text)
            return True
        except requests.exceptions.RequestException as e:
            print("Unable to get sernsor data")
            return False

def broadcast_alive():
    data_payload = {"device_name": args.name, "interest": args.interest}
    data_payload = json.dumps(data_payload)
    try:
        response = requests.post(node_address,headers=headers, data=data_payload, timeout=1)
        response.raise_for_status()  # Raises an HTTPError for bad responses (4xx and 5xx)
        # print(f"Success! Status Code: {response.status_code}")
        print(response.json())  # Assuming the response contains JSON data
    except requests.exceptions.RequestException as e:
        print("Unable to register with server")

# def recv_data():
#     # base_url = "http://"+hostname[:-2]+"{}"+".berry.scss.tcd.ie:33696/registernodes"
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
#         # data_url ="http://rasp-0"+str(IPAddr)[-2:]+".berry.scss.tcd.ie:33696/getdata"
#         data_url ="http://localhost:33696/getdata"
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
        pass
except (KeyboardInterrupt, SystemExit):
    # Cleanly shut down the scheduler
    scheduler.shutdown()
    print("Script terminated.")
