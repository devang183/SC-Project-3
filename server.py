import json
import random
from flask import Flask, jsonify, request, send_file
import requests
import time
import atexit
from apscheduler.schedulers.background import BackgroundScheduler
from os import walk
import socket
import encryptionCompression as ec
import base64
from base64 import b64decode
import tpm as ss

hostname = socket.gethostname()
IPAddr = socket.gethostbyname(hostname)
 
app = Flask(__name__)
ip_data={}
ip_port={}

def syncwithnodes():
    # print("chalu hogaya bhai")
    # print(filenames)
    # print(type(filenames))
    filenames = next(walk("data/"), (None, None, []))[2]  # [] if no file
    base_url = "http://"+hostname[:-2]+"{}"+".berry.scss.tcd.ie:33696/registernodes"
    data_payload=','.join(filenames)
    headers = {
    'Content-Type': 'text/plain'
    }
    for i in range(1, 50): # ip range
        try:
            # print("trying ip: ",base_url.format(i))
            response = requests.post(base_url.format(i), headers=headers, data=data_payload, timeout=1)
        except:
            n = 0
    print(ip_data)
    # print(ip_port)
    return True

@app.route('/registernodes', methods=['POST'])
def register_node():
    if ("http://rasp-0"+str(request.remote_addr)[-2:]+".berry.scss.tcd.ie") not in ip_data or request.data.decode('UTF-8') not in ip_data.values():
        ip_data.update({"http://rasp-0"+str(request.remote_addr)[-2:]+".berry.scss.tcd.ie":request.data.decode('UTF-8')})
        print("Registered Node with IP: ",request.remote_addr)
    if ("http://rasp-0"+str(request.remote_addr)[-2:]+".berry.scss.tcd.ie") not in ip_port or request.environ['REMOTE_PORT'] not in ip_port.values():
        ip_port.update({"http://rasp-0"+str(request.remote_addr)[-2:]+".berry.scss.tcd.ie":request.environ['REMOTE_PORT']})
        # print("updated port")
    print(request.environ['REMOTE_PORT'])
    return jsonify({'ip': request.remote_addr}), 200


#-----------------------SECURE STORAGE(STORAGE AND GET)--------------------------

@app.route('/getallnodes', methods=['POST'])
def allnodes():
    print(ip_data)
    print(ip_port)
    storage.save_data(request.remote_addr)
    
    return jsonify({'ip': request.remote_addr}), 200

@app.route('/read_secure_storage', methods=['GET'])
def read_secure_storage():
    retrieved_data = storage.retrieve_data()
    print("Retrieved Data:", retrieved_data)
    return jsonify({retrieved_data}), 200


#-----------------------ENCRYPTION AND COMPRESSION--------------------------
@app.route('/share_private_key', methods=['POST'])
def share_private_key_function():

    #Only the selected IPs will be able to download the file

    try:
        return send_file('private_key.pem', as_attachment=True)
    except FileNotFoundError:
        pass  # Do nothing here or handle the exception

    # If the loop completes without returning, handle the case when the file is not found
    return "File not found", 404


@app.route('/broadcast', methods=['POST'])
def BroadCastTextData():
    
    csv_data = request.data.decode('utf-8')
    loaded_public_key = ec.load_key_from_file('public_key.pem', is_private=False)   
    compressed_data = ec.compress_text(csv_data) 
    encrypted_data = ec.encrypt(compressed_data, loaded_public_key)
    encoded_data = base64.b64encode(encrypted_data).decode('utf-8')
    with open('encrypted_data.txt', 'w') as file:
        file.write(encoded_data)
    return jsonify({"data": encoded_data})

@app.route('/read_data', methods=['POST'])
def read_data():
    data = request.json.get('data')
    print("Encrypted data:", data)
    loaded_private_key = ec.load_key_from_file('private_key.pem')
    decrypted_message = ec.decrypt(b64decode(data), loaded_private_key)
    decompressed_text = ec.decompress_text(decrypted_message)
    print("Decrypted data:", decompressed_text)
    return decompressed_text
#--------------------------------------------



@app.route('/getdata', methods=['POST'])
def getdata():
    filenames = next(walk("data/"), (None, None, []))[2]  # [] if no file
    interest_packet=request.data.decode('UTF-8')
    print("Interest packet = ",interest_packet)
    if interest_packet in filenames:
        print("Found in local")
        f = open("data/"+interest_packet, 'r')
        interest_data = f.read()
        f.close()
        return interest_data
    print("not found in local")
    for key, value in ip_data.items():
        if interest_packet in value.split(','):
            ip_withdata=key
            # print(ip_withdata)
            data_url = str(ip_withdata)+":33696/getdata"
            payload = interest_packet
            headers = {
            'Content-Type': 'text/plain'
            }
            try:
                response = requests.post(data_url, headers=headers, data=payload, timeout=0.5)
                print(response.text)
            except:
                print("Error, the Node is not up: ",data_url)
            return response.text
    print("Not Found")
    return 404

if __name__ == '__main__':
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=syncwithnodes, trigger="interval", seconds=20)
    #------------------
    private_key, public_key = ec.generate_key_pair()
    storage = ss.SecureStorage()
    
    ec.save_key_to_file(private_key, 'private_key.pem')
    ec.save_key_to_file(public_key, 'public_key.pem')

    #--------------------------
    # Shut down the scheduler when exiting the app
    atexit.register(lambda: scheduler.shutdown())
    # syncwithnodes()
    scheduler.start()
    app.run(host=IPAddr,port=33696)
