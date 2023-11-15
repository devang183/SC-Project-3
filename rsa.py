import random
from Crypto.PublicKey import RSA

def generate_rsa_keys(key_size):
    """Generates a pair of RSA keys, a public key and a private key.

    Args:
        key_size: The size of the keys in bits.

    Returns:
        A tuple of (public_key, private_key).
    """

    random_generator = random.SystemRandom()
    key = RSA.generate(key_size, random_generator)
    public_key = key.publickey()
    return public_key, key

def encrypt_message(public_key, message):
    """Encrypts a message using the given public key.

    Args:
        public_key: The public key to use for encryption.
        message: The message to encrypt.

    Returns:
        The encrypted message.
    """

    encrypted_message = public_key.encrypt(message.encode('utf-8'), 32)
    return encrypted_message

def decrypt_message(private_key, encrypted_message):
    """Decrypts a message using the given private key.

    Args:
        private_key: The private key to use for decryption.
        encrypted_message: The encrypted message to decrypt.

    Returns:
        The decrypted message.
    """

    decrypted_message = private_key.decrypt(encrypted_message)
    return decrypted_message.decode('utf-8')

# Generate a pair of RSA keys
public_key, private_key = generate_rsa_keys(2048)

# Encrypt a message
message = "This is a secret message."
encrypted_message = encrypt_message(public_key, message)

# Decrypt the message
decrypted_message = decrypt_message(private_key, encrypted_message)

print(decrypted_message)