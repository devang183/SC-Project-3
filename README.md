# SC-Project-3
APIs summary report by Sambit Sourav:

# Provisioning (RSA and TPM)
   - Create a AES Key
   - Discover "Known" IPs and save it in Secure Storage(TPM)
       - [POST] /getallnodes
   - Retrive Authentic IPs from Secure Storage
       - [GET]  /read_secure_storage
   - Send Private Key to the authenticated IPs
       - [POST] /share_key
# Communication (GZip, Public and Private Key)
   - All the messages for communication between nodes is encrypted and compressed( for demo we hit this API) 
       - [POST] /broadcast
         - Expects plain text in body
   - Decrypt sent messages, only the nodes having Private Key can decrypt
       - [POST] /read_data
