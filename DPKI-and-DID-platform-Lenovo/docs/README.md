# dpki&did-platform-lenovo
## Start the platform!

double click start-dpki.bat


  
**Install OpenSSL(must):**

This project uses OpenSSL for cryptographic operations (due to challenges with JavaScript’s native cryptography plugins). The keys are generated based on this, certificates are created using the keys, and the certificate authentication process is entirely managed on-chain.  
You can download it from [openssl install](https://slproweb.com/products/Win32OpenSSL.html). The lightweight version is sufficient. After installation, add its /bin folder to your system path (It should be prioritized in the path list to prevent errors).
```
openssl version  //Check that the OpenSSL version is correct
```
  
## Configuration File(must):
***Please note:*** The following default configurations in  ```DPKI-config.json``` must be synchronized with all UE nodes before proceeding with any experimental steps:  
```
{
  "Blockchain": {
    // Blockchain node address, typically the host's address. Use .\omni-cli net peer info to check, or ipconfig. Portal is locked to 8545
    "providerUrl": "http://LOCAL:8545",
    
    // Genesis address, ensure this address has gas available. This account is your genesis account of blockchain. If you use onmichain in our project this remains unchanged.
    "account": "0xab7F5238cbEfB02062241cf979e4994b656FB944",

    // The private key of the genesis address. Ideally, each UE node should have its own account, but to simplify, the genesis address is used.
    "privateKey": "0x73e66f099144f820753aa3a5e131785b528081da572e16339fcd02de05de719e"
  },

  "contract": {
    // Default setting, no need to change.
    "abiPath": "./authentication.abi",

    // Same as above.
    "bytecodePath": "./authentication.code",

    // Contract address. Running the deploycontract function in DPKI.js will deploy the contract. Fill in the contract address here. If you load our chain this contract can be directly used.
    "address": "0x99c7FDb06Bf5832Ef13dCA9aa67Da8EfBE2Cba35"
  },

  "Servernetwork": {
    // Host address, note that this is the SEU LAN address.
    "serverHost": "YOUR IP",   **----this is where you must change based on your own IP and the portal MUST be open**

    // The port being listened to. The default port for the host is 12349, and for UE it’s 12348.
    "serverPort": 12349
  }
}

```
  
Afterward, execute the corresponding .exe files to complete the operation. On the CA (Certificate Authority) side, there are two executable files, ```Server-CA``` and ```DPKI-CA```, while on the UE (User Equipment) side, there are ```Server-UE``` and ```DPKI-UE```.

With this setup, both CA and UE can perform certificate operations within the SEU LAN (or a local network), where one CA and two UE nodes are enough for the simplest environment setup. This process can also be performed locally.



## Experimental Procedure:

## Pre-Deployment  
**Run the underlying blockchain platform:**
```
./omni.exe -f omni.toml   // Start the blockchain platform
./omni-cli net peer info     // Check status and IP
```
**Create and unlock the blockchain wallet:**
```
// If no wallet exists, create one using the following bash commands:
.\omni-cli seed generate -l 0
// Password must include letters and numbers, and should be noted carefully, otherwise the entire wallet will need to be reset.
.\omni-cli seed save -s 'generated seed phrase' -p password  
// Unlock the wallet. Unlocking is necessary to create accounts.
.\omni-cli wallet unlock -p password -t 0

test-steps(if the process above is not working)
### 1. Start the listeners on both ends (CA and UE):


A listener has been set up on both the UE side and the CA side. This listener allows communication between users within the SEU LAN; otherwise, a port configuration is required.
```
./Server-CA  
./Server-UE
```
  
### 2. Initialize the root certificate and upload it on-chain (CA):

```
./DPKI-CA initial -ca_name string -ca_label string  
```
The ```string``` in the commands represents a placeholder and needs to be replaced with the actual name or value. 

Generally, the ```ca_name``` and ```ca_label``` are the same. The label is used as the key in on-chain registration, while the value stores the certificate information. Due to CA-specific functionality, custom labels are supported, but in practice, keeping ca_name and ca_label consistent is recommended.
  
### 3. UE submits a CSR (UE to CA):  
```
./DPKI-UE request -ue_name string                  
```
UE cannot customize the label. The root address is specified in the ```DPKI-config``` file and corresponds to the single-node blockchain’s host. Before initiating this request, ensure that the config file is properly synchronized with all UE nodes.
  
### 4. CA signs the certificate (CA to UE):
```
./DPKI-CA register -ca_name string -ue_name string   
```
CA signs the UE’s certificate (corresponding to the CSR) and uploads the certificate along with related information (validity period, public key, corresponding Ethereum address, etc.) on-chain. This is stored in the contract as a mapping between the CA name and certificate details. Note that once a CA name is registered on-chain, it cannot be reused.

  
### 5. CA updates the certificate (CA to UE):
```
./DPKI-CA update -ca_name string -ue_name string     
```
The logic is similar to register, but update allows overwriting an existing certificate with the same label, typically used to refresh the validity period. 
  
### 6. CA revokes the certificate (CA to UE):
```
./DPKI-CA revoke -ue_name string                     
```
This will invalidate the certificate upon verification.
  
### 7. UE updates the address list (CA to UE):
```
./DPKI-UE updatelist                                 
```
This updates the local ```DPKI-config``` file. This feature currently serves as a method to retrieve other UE addresses from the CA.
  
### 8. UE authentication between two UEs (UE1 to UE2):
```
./DPKI-UE authenticationreq -ue_name string -target string         
```
The ```ue_name``` is used to differentiate between multiple certificates that may exist locally. The ```target``` refers to the name of the other UE, which corresponds to the address defined in the config file. 

The authentication logic is as follows:

a) UE1 generates a signature, signing its Ethereum address with its private key, and attaches the certificate. This is then sent to UE2.

b) UE2’s listener receives the message.

c) UE2 passes this information to the smart contract.

The smart contract verifies the following: 
- Whether the certificate matches the one in the certificate repository (hash match).
- Whether the certificate's timestamp (stored on-chain) has exceeded the current blockchain timestamp.
- Whether the recovered address from the certificate signature matches (i.e., signature verification).
- Whether the certificate is valid (whether it has been revoked).

These checks occur in sequence. If any condition fails, the error returned will be for the last check that failed (with a Chinese error message for the most critical failure).
If all checks pass, both the UE1 client and the UE2 listener will receive a successful authentication message.                                                                                                                                                                                       
