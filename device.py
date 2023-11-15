import requests
from os import walk
import json
import argparse
import socket
import atexit
from apscheduler.schedulers.background import BackgroundScheduler
import joblib
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

#Fully Working Code(tested) - Devang
# Load the trained model
model = joblib.load('model.pkl')
    
from flask import request, jsonify
import pandas as pd

def predict(data):
    features = data[["Temperature", "Rainfall", "Precipitation", "Longitude", "Latitude", "Speed", "Acceleration", "Steering Angle", "Brake Pressure", "Throttle Position", "Gear"]]
    prediction = model.predict(features)
    return prediction.tolist()  # Convert NumPy array to a list

@app.route('/predict', methods=['POST'])
def make_prediction():
    new_data = request.get_json()

    # Check if the required fields are present in the DataFrame
    if isinstance(new_data, list):
        # If new_data is a list, convert it to a DataFrame
        new_data = pd.DataFrame(new_data)

    # Check if the required fields are present in the DataFrame
    if all(field in new_data.columns for field in ["Temperature", "Rainfall", "Precipitation", "Longitude", "Latitude", "Speed", "Acceleration", "Steering Angle", "Brake Pressure", "Throttle Position", "Gear"]):
        # Make a prediction
        result = predict(new_data)

        # Create a list of dictionaries in the specified format
        output_list = []
        for i in range(len(new_data)):
            output_dict = {
                "Temperature": new_data.loc[i, "Temperature"],
                "Rainfall": new_data.loc[i, "Rainfall"],
                "Precipitation": new_data.loc[i, "Precipitation"],
                "Longitude": new_data.loc[i, "Longitude"],
                "Latitude": new_data.loc[i, "Latitude"],
                "Speed": new_data.loc[i, "Speed"],
                "Acceleration": new_data.loc[i,"Acceleration"],
                "Steering Angle": new_data.loc[i, "Steering Angle"],
                "Brake Pressure": new_data.loc[i, "Brake Pressure"],
                "Throttle Position": new_data.loc[i, "Throttle Position"],
                "Gear": new_data.loc[i, "Gear"],
                "Label": round(result[i])
            }
            output_list.append(output_dict)

        # Return the result as JSON
        return jsonify(output_list)

    else:
        return jsonify({"error": "Invalid input format"}), 400

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
