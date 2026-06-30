# omni-did

### 0. First run - Deploy the smart contract

The underlying blockchain environment  is exactly the same as the DPKI system. On the Windows operating system, we can directly double - click `omnichain.exe` to start Omnichain.

When using OmniDID for the first time, we need to run `DeployContract.java` to deploy the smart contract. After obtaining the contract address, we should configure it in the `contract.address` configuration item of `application.properties`. This step is not required for subsequent use.

Since I have deployed the smart contract in advance and completed the configuration, I can package the code and start the OmniDID system in the command line:

```sh
java -jar omni-did-0.0.1-SNAPSHOT.jar
```

This console will serve as the issuer/verifier server.

### 1. Generate DID and DID document

Here, I use the interface call testing tool Postman. This window is used by the UE to call the DID service, which is essentially the same as making a direct request in the browser. Each call will return a different DID. 

```
http://localhost:8080/did
```

return

```json
{
    "code": 1,
    "msg": "success",
    "data": "did:omni:b6343195a0784a6db0"
}
```

Executing this step will generate a DID. Meanwhile, the issuer/verifier server will generate a DID document, put the DID and the DID document on the block-chain, and return the transaction hash.

### 2. On - chain query
After obtaining the DID, we can query the DID document on the blockchain and will get the DID document.
```
http://localhost:8080/did/did:omni:b6343195a0784a6db0
```

return

```json
{
    "code": 1,
    "msg": "success",
    "data": {
        "@context": [
            "https://www.w3.org/ns/did/v1"
        ],
        "id": "did:omni:b6343195a0784a6db0",
        "verificationMethod": [
            {
                "type": "Ed25519VerificationKey2018",
                "id": "did:omni:b6343195a0784a6db0#key-1",
                "publicKeyBase58": "FyfKP2HvTKqDZQzvyL38yXH7bExmwofxHf2NR5BrcGf1"
            }
        ],
        "service": [
            {
                "type": "ServiceEndpointProxyService",
                "serviceEndpoint": "https://myservice.com/myendpoint"
            }
        ]
    }
}
```

If an unregistered DID is entered, no result will be returned.
### 3. Generate VC
We fill in the DID generated just now and relevant attribute fields, such as "Jackson" and "29". Then we can obtain the VC in JWT format and the VC in JSON format and store them locally.
```
http://localhost:8080/vc/user-attribute?did=did:omni:85d679aa641544e1ab&name=jack&age=24
```

return

```json
{
    "code": 1,
    "msg": "success",
    "data": "eyJ0eXAiOiJKV1QiLCJhbGciOiJFZERTQSJ9.eyJzdWIiOiJkaWQ6b21uaTpiNjM0MzE5NWEwNzg0YTZkYjAiLCJuYmYiOjE3Mzk0NjIxNjEsImlzcyI6ImRpZDpleGFtcGxlOjc2ZTEyZWM3MTJlYmM2ZjFjMjIxZWJmZWIxZiIsImV4cCI6MTgwMjUzNDE2MSwidmMiOnsiQGNvbnRleHQiOlsiaHR0cHM6Ly93d3cudzMub3JnLzIwMTgvY3JlZGVudGlhbHMvdjEiLCJodHRwczovL3d3dy53My5vcmcvMjAxOC9jcmVkZW50aWFscy9leGFtcGxlcy92MSJdLCJ0eXBlIjpbIlZlcmlmaWFibGVDcmVkZW50aWFsIiwiVW5pdmVyc2l0eURlZ3JlZUNyZWRlbnRpYWwiXSwiY3JlZGVudGlhbFN1YmplY3QiOnsib3JnYW5pemF0aW9uIjoiVGVzdCBVbml2ZXJzaXR5IiwiVXNlciBBdHRyaWJ1dGUgVkMiOnsibmFtZSI6ImphY2siLCJhZ2UiOiIyNCJ9fX0sImp0aSI6Imh0dHA6Ly9leGFtcGxlLmVkdS9jcmVkZW50aWFscy8zNzMyIn0.rogvrWsj74-8knDjwb9z1SfCWc85rmtXiGdKNVwkbq8bIyGG3wURY9b0C6r-9Hf7fa-c33lSAqoIhLpiXcqECQ"
}
```

Locally saved VC

```json
{
  "@context" : [ "https://www.w3.org/2018/credentials/v1", "https://www.w3.org/2018/credentials/examples/v1" ],
  "type" : [ "VerifiableCredential", "UniversityDegreeCredential" ],
  "id" : "http://example.edu/credentials/3732",
  "issuer" : "did:example:76e12ec712ebc6f1c221ebfeb1f",
  "issuanceDate" : "2025-02-13T15:56:01Z",
  "expirationDate" : "2027-02-13T15:56:01Z",
  "credentialSubject" : {
    "id" : "did:omni:b6343195a0784a6db0",
    "organization" : "Test University",
    "User Attribute VC" : {
      "name" : "jack",
      "age" : "24"
    }
  }
}
```

### 4. Verify VC
We use the JWT as a parameter to request the verification interface, and the verification result will be returned.

```
http://localhost:8080/vc/verify-jwt?jwtString=eyJ0eXAiOiJKV1QiLCJhbGciOiJFZERTQSJ9.eyJzdWIiOiJkaWQ6b21uaTo4NWQ2NzlhYTY0MTU0NGUxYWIiLCJuYmYiOjE3Mzk0NTQxNDYsImlzcyI6ImRpZDpleGFtcGxlOjc2ZTEyZWM3MTJlYmM2ZjFjMjIxZWJmZWIxZiIsImV4cCI6MTgwMjUyNjE0NiwidmMiOnsiQGNvbnRleHQiOlsiaHR0cHM6Ly93d3cudzMub3JnLzIwMTgvY3JlZGVudGlhbHMvdjEiLCJodHRwczovL3d3dy53My5vcmcvMjAxOC9jcmVkZW50aWFscy9leGFtcGxlcy92MSJdLCJ0eXBlIjpbIlZlcmlmaWFibGVDcmVkZW50aWFsIiwiVW5pdmVyc2l0eURlZ3JlZUNyZWRlbnRpYWwiXSwiY3JlZGVudGlhbFN1YmplY3QiOnsib3JnYW5pemF0aW9uIjoiVGVzdCBVbml2ZXJzaXR5IiwiVXNlciBBdHRyaWJ1dGUgVkMiOnsibmFtZSI6ImphY2siLCJhZ2UiOiIyNCJ9fX0sImp0aSI6Imh0dHA6Ly9leGFtcGxlLmVkdS9jcmVkZW50aWFscy8zNzMyIn0.HL2CoxA2rZN8YIXJ_Kt3EUIT7nwjxzMDJ4uScJ5_peiLl-MJB80nhxwGsb8686QYwLvbTMyKS9HffVc0dtEECA
```

retrurn

```json
{
    "code": 1,
    "msg": "success",
    "data": true
}
```

Any tampering will make the verification result false.

### 5. Retrieve VC content
We also fill in the JWT and initiate a request. The issuer/verifier server will first verify the correctness of the JWT and then parse the content of the JWT.

retrun



```json
{
    "code": 1,
    "msg": "success",
    "data": {
        "@context": [
            "https://www.w3.org/2018/credentials/v1",
            "https://www.w3.org/2018/credentials/examples/v1"
        ],
        "type": [
            "VerifiableCredential",
            "UniversityDegreeCredential"
        ],
        "id": "http://example.edu/credentials/3732",
        "issuer": "did:example:76e12ec712ebc6f1c221ebfeb1f",
        "issuanceDate": "2025-02-13T15:56:01Z",
        "expirationDate": "2027-02-13T15:56:01Z",
        "credentialSubject": {
            "organization": "Test University",
            "User Attribute VC": {
                "name": "jack",
                "age": "24"
            },
            "id": "did:omni:b6343195a0784a6db0"
        }
    }
}
```

So far, we have completed the generation of DIDs and DID documents, as well as the generation and verification of VCs. 