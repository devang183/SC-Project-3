from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes
from cryptography.fernet import Fernet
import gzip


#-----------RSA, AES and Compression (Sambit)----------------------------------
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
        message,
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
    return plaintext

# Compression of file

def compress_file(input_file, output_file):
    with open(input_file, 'rb') as f_in, gzip.open(output_file, 'wb') as f_out:
        f_out.writelines(f_in)

# Example usage
input_filename = 'your_encrypted_file.txt'
output_filename = 'compressed_encrypted_file.gz'

def decompress_file(input_file, output_file):
    with gzip.open(input_file, 'rb') as f_in, open(output_file, 'wb') as f_out:
        f_out.write(f_in.read())


#Text Compression
import zlib

def compress_text(text):
    return zlib.compress(text.encode('utf-8'))

def decompress_text(compressed_data):
    decompressed_text = zlib.decompress(compressed_data).decode('utf-8')
    return decompressed_text

#-----------AES--------------------------------------------------
def generate_aes_key():
    return Fernet.generate_key()

def save_aes_key_to_file(key, filename):
    with open(filename, 'wb') as key_file:
        key_file.write(key)

def load_aes_key_from_file(filename):
    with open(filename, 'rb') as key_file:
        return key_file.read()

def encrypt_message(message, key):
    cipher = Fernet(key)
    ciphertext = cipher.encrypt(message)
    return ciphertext

def decrypt_message(ciphertext, key):
    cipher = Fernet(key)
    plaintext = cipher.decrypt(ciphertext)
    return plaintext
