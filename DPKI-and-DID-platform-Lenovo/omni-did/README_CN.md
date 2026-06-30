# omni-did

### 0. 第一次运行——部署智能合约

区块链底层环境平台与dpki系统完全相同，在Windows操作系统下，我们可以直接双击omnichain.exe来启动omnichain。

当我们第一次使用omnidid，需要运行DeployContract.java部署智能合约，获取到合约地址，配置在application.properties的contract.address配置项中，后续使用无需此步骤。

我已经事先部署好了智能合约并完成了配置，就可以将代码打包，在命令行启动omnidid系统

```sh
java -jar omni-did-0.0.1-SNAPSHOT.jar
```

这个控制台将作为issuer/verifier服务器

### 1. 生成did和did文档

我这里使用了接口调用测试工具postman，这个窗口作为UE调用did服务，本质上和在浏览器直接请求是一样的，每次都会返回不同的did。

```
http://localhost:8080/did
```

返回结果

```json
{
    "code": 1,
    "msg": "success",
    "data": "did:omni:b6343195a0784a6db0"
}
```

执行这一步会生成did，同时issuer/verifier服务器会生成did文档并将did和地点文档上链，返回交易哈希

### 2. 链上查询

我们获取到did后可以进行链上的did文档查询，我们将会获取到did文档

```
http://localhost:8080/did/did:omni:b6343195a0784a6db0
```

返回结果

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

如果输入了未注册的did，就不会有结果返回

### 3. 生成vc

我们填入刚刚生成的did，以及相关的属性字段，如jackson，29，就可以获取到jwt形式的vc和json格式的vc存储在本地，

```
http://localhost:8080/vc/user-attribute?did=did:omni:85d679aa641544e1ab&name=jack&age=24
```

返回结果

```json
{
    "code": 1,
    "msg": "success",
    "data": "eyJ0eXAiOiJKV1QiLCJhbGciOiJFZERTQSJ9.eyJzdWIiOiJkaWQ6b21uaTpiNjM0MzE5NWEwNzg0YTZkYjAiLCJuYmYiOjE3Mzk0NjIxNjEsImlzcyI6ImRpZDpleGFtcGxlOjc2ZTEyZWM3MTJlYmM2ZjFjMjIxZWJmZWIxZiIsImV4cCI6MTgwMjUzNDE2MSwidmMiOnsiQGNvbnRleHQiOlsiaHR0cHM6Ly93d3cudzMub3JnLzIwMTgvY3JlZGVudGlhbHMvdjEiLCJodHRwczovL3d3dy53My5vcmcvMjAxOC9jcmVkZW50aWFscy9leGFtcGxlcy92MSJdLCJ0eXBlIjpbIlZlcmlmaWFibGVDcmVkZW50aWFsIiwiVW5pdmVyc2l0eURlZ3JlZUNyZWRlbnRpYWwiXSwiY3JlZGVudGlhbFN1YmplY3QiOnsib3JnYW5pemF0aW9uIjoiVGVzdCBVbml2ZXJzaXR5IiwiVXNlciBBdHRyaWJ1dGUgVkMiOnsibmFtZSI6ImphY2siLCJhZ2UiOiIyNCJ9fX0sImp0aSI6Imh0dHA6Ly9leGFtcGxlLmVkdS9jcmVkZW50aWFscy8zNzMyIn0.rogvrWsj74-8knDjwb9z1SfCWc85rmtXiGdKNVwkbq8bIyGG3wURY9b0C6r-9Hf7fa-c33lSAqoIhLpiXcqECQ"
}
```

本地留存vc

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

### 4. 验证vc

我们将jwt作为参数，请求验证接口，会返回验证结果

```
http://localhost:8080/vc/verify-jwt?jwtString=eyJ0eXAiOiJKV1QiLCJhbGciOiJFZERTQSJ9.eyJzdWIiOiJkaWQ6b21uaTo4NWQ2NzlhYTY0MTU0NGUxYWIiLCJuYmYiOjE3Mzk0NTQxNDYsImlzcyI6ImRpZDpleGFtcGxlOjc2ZTEyZWM3MTJlYmM2ZjFjMjIxZWJmZWIxZiIsImV4cCI6MTgwMjUyNjE0NiwidmMiOnsiQGNvbnRleHQiOlsiaHR0cHM6Ly93d3cudzMub3JnLzIwMTgvY3JlZGVudGlhbHMvdjEiLCJodHRwczovL3d3dy53My5vcmcvMjAxOC9jcmVkZW50aWFscy9leGFtcGxlcy92MSJdLCJ0eXBlIjpbIlZlcmlmaWFibGVDcmVkZW50aWFsIiwiVW5pdmVyc2l0eURlZ3JlZUNyZWRlbnRpYWwiXSwiY3JlZGVudGlhbFN1YmplY3QiOnsib3JnYW5pemF0aW9uIjoiVGVzdCBVbml2ZXJzaXR5IiwiVXNlciBBdHRyaWJ1dGUgVkMiOnsibmFtZSI6ImphY2siLCJhZ2UiOiIyNCJ9fX0sImp0aSI6Imh0dHA6Ly9leGFtcGxlLmVkdS9jcmVkZW50aWFscy8zNzMyIn0.HL2CoxA2rZN8YIXJ_Kt3EUIT7nwjxzMDJ4uScJ5_peiLl-MJB80nhxwGsb8686QYwLvbTMyKS9HffVc0dtEECA
```

返回结果

```json
{
    "code": 1,
    "msg": "success",
    "data": true
}
```

任何的篡改将使验证结果为false

### 5. 获取vc内容

我们同样填入jwt，发起请求，issuer/verifier服务器会首先验证jwt的正确性，然后解析jwt内容

返回结果

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

至此我们完成的了did、did文档的生成，vc的生成和验证。