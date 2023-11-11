import json
import random
from flask import Flask, jsonify, request, send_file
import requests
import time
import atexit
from apscheduler.schedulers.background import BackgroundScheduler
from os import walk
import socket


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


@app.route('/getallnodes', methods=['POST'])
def allnodes():
    print(ip_data)
    print(ip_port)
    return jsonify({'ip': request.remote_addr}), 200


#-----------------------ENCRYPTION AND COMPRESSION--------------------------

#Fully Working Code(tested) ---- please ignore this area --- I will clean up on integration -Sambit
@app.route('/share_private_key', methods=['POST'])
def share_private_key_function():

    #Only the selected IPs will be able to download the file
    # remove the for loop if you want to share the file with all the IPs

    try:
        return send_file('private_key.pem', as_attachment=True)
    except FileNotFoundError:
        pass  # Do nothing here or handle the exception

    # If the loop completes without returning, handle the case when the file is not found
    return "File not found", 404

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes
import gzip

def generate_key_pair():
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )
    public_key = private_key.public_key()

    return private_key, public_key

def save_key_to_file(key, filename):
    with open(filename, 'wb') as key_file:
        if isinstance(key, rsa.RSAPrivateKey):
            key_bytes = key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )
        else:
            key_bytes = key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
        key_file.write(key_bytes)

def load_key_from_file(filename, is_private=True):
    with open(filename, 'rb') as key_file:
        key_data = key_file.read()
        if is_private:
            return serialization.load_pem_private_key(key_data, password=None, backend=default_backend())
        else:
            return serialization.load_pem_public_key(key_data, backend=default_backend())

def encrypt(message, public_key):
    ciphertext = public_key.encrypt(
        message.encode('utf-8'),
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    return ciphertext

def decrypt(ciphertext, private_key):
    plaintext = private_key.decrypt(
        ciphertext,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    return plaintext.decode('utf-8')



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
    private_key, public_key = generate_key_pair()

    save_key_to_file(private_key, 'private_key.pem')
    save_key_to_file(public_key, 'public_key.pem')

    loaded_private_key = load_key_from_file('private_key.pem')
    loaded_public_key = load_key_from_file('public_key.pem', is_private=False)

    message = "Hello, RSA Encryption!"

    ciphertext = encrypt(message, loaded_public_key)
    print("Encrypted message:", ciphertext)

    decrypted_message = decrypt(ciphertext, loaded_private_key)
    print("Decrypted message:", decrypted_message)
    # Print the decrypted message.
    print(decrypted_message)
    #--------------------------
    # Shut down the scheduler when exiting the app
    atexit.register(lambda: scheduler.shutdown())
    # syncwithnodes()
    scheduler.start()
    app.run(host=IPAddr,port=33696)
