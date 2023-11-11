

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
    compressed_data = zlib.compress(text.encode('utf-8'))
    return compressed_data

def decompress_text(compressed_data):
    decompressed_text = zlib.decompress(compressed_data).decode('utf-8')
    return decompressed_text

# Example usage
original_text = "This is an example text to be compressed using Gzip."
print("Original Text:", original_text)

# Compress the text
compressed_data = compress_text(original_text)
print("Compressed Data:", compressed_data)

# Decompress the data
decompressed_text = decompress_text(compressed_data)
print("Decompressed Text:", decompressed_text)


#--------------------------------------------


if __name__ == '__main__':
    
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
