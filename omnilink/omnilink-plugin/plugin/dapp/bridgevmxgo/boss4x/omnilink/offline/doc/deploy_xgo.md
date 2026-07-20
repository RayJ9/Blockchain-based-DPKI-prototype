###  离线部署 xgo 合约及各操作
*** 

#### 基础步骤
* 离线创建并签名交易 `./evmxgoboss4x omnilink offline create ... -k ...`
* 在线发送签名后文件 `./evmxgoboss4x omnilink offline send -f ...` 

拼凑 evmxgoboss4x 命令

./evmxgoboss4x --rpc_laddr http://${docker_omnilink_ip}:8901 --paraName user.p.para. --chainID 0
```
--chainID int32      chain id, default to 0
--expire string      transaction expire time (optional) (default "120m")
--paraName string    平行链名称
--rpc_laddr string   平行链 url (default "https://localhost:8801")
```
*** 

#### 离线部署 omnilink 跨链合约
* 离线创建并签名交易
```
交易1: 部署合约 Valset
交易2: 部署合约 EthereumBridge
交易3: 部署合约 Oracle
交易4: 部署合约 BridgeBank
交易5: 设置合约 set BridgeBank to EthBridge 
交易6: 设置合约 set Oracle to EthBridge 
交易7: 部署合约 BridgeRegistry 

命令：
./evmxgoboss4x omnilink offline create -f 1 -k "${omnilinkDeployKey}" -n "deploy crossx to omnilink" -r "${omnilinkDeployAddr}, [${omnilinkValidatora}, ${omnilinkValidatorb}, ${omnilinkValidatorc}, ${omnilinkValidatord}], [96, 1, 1, 1]"
    
参数说明：
  -f, --fee float         手续费
  -k, --key string        部署合约的私钥
  -n, --note string       交易备注
  -r, --valset string     valset 合约参数, 格式: 'addr, [addr, addr, addr, addr], [25, 25, 25, 25]','部署地址,[验证者A地址, ...],[验证者A权重, ...]'
输出:
把交易信息写入 deployBridgevmxgo2Omnilink.txt 文件中
```

* 发送签名后文件
```
./evmxgoboss4x omnilink offline send -f deployBridgevmxgo2Omnilink.txt
```

***

#### 设置 symbol 允许被 lock
* 在线创建交易
```
命令：
./evmxgoboss4x omnilink offline create_add_lock_list -s ETH -t "${omnilinkEthBridgeTokenAddr}" -c "${XgoOmnilinkBridgeBank}" -k "${omnilinkDeployKey}" -f 1

参数说明：
  -c, --contract string   创建的 xgo bridgebank 合约地址
  -f, --fee float         手续费
  -k, --key string        部署合约的私钥
  -n, --note string       交易备注
  -s, --symbol string     token symbol
  -t, --token string      omnilink evm bridge token 地址  

输出
tx is written to file:  create_add_lock_list.txt
```
***

#### manage 设置 bridgevmxgo 合约地址
```shell
# 创建交易
# XgoOmnilinkBridgeBank 部署的 xgo BridgeBank 合约地址
curl -s --data-binary '{"jsonrpc":"2.0","id":2,"method":"Omnilink.CreateTransaction","params":[{"execer":"manage","actionName":"Modify","payload":{"key":"bridgevmxgo-contract-addr","value":"{\"address\":\"'"${XgoOmnilinkBridgeBank}"'\"}","op":"add","addr":""}}]}' -H 'content-type:text/plain;' "http://${docker_omnilink_ip}:8901"
# 用平行链管理者地址签名
./omnilink_cli wallet sign -k "$paraMainAddrKey" -d "${tx}"
```

#### manage add symbol
```shell
# 创建交易
# symbol 需要增加的 symbol
# bridgeTokenAddr omnilink 对应的 BridgeToken 地址, 例如:omnilinkEthBridgeTokenAddr
curl -s --data-binary '{"jsonrpc":"2.0","id":2,"method":"Omnilink.CreateTransaction","params":[{"execer":"manage","actionName":"Modify","payload":{"key":"evmxgo-mint-'"${symbol}"'","value":"{\"address\":\"'"${bridgeTokenAddr}"'\",\"precision\":8,\"introduction\":\"symbol:'"${symbol}"', bridgeTokenAddr:'"${bridgeTokenAddr}"'\"}","op":"add","addr":""}}]}' -H 'content-type:text/plain;' "http://${docker_omnilink_ip}:8901"

# 用平行链管理者地址签名
./omnilink_cli wallet sign -k "$paraMainAddrKey" -d "${tx}"
```
