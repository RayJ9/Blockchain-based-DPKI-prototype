# chain33_dpki_lenovo  

-------
9.6 jr  
first establish  
简单实现了合约-分类-map存储的功能  
使用online-map-demo可以试一下功能，生成带add、update、revoke标签的交易并丢给合约，合约进行分类后修改链上的map，和local-db的功能一样（local是本地的数据库，没有过合约） 
合约是testcontract的三个文件，现在文件还很乱，后期会整理，先玩一玩试试  
   
让demo跑起来之准备工作  
1.安装node.js保姆级教程：https://blog.csdn.net/WHF__/article/details/129362462  以及可能遇到的问题的解决方案：https://blog.csdn.net/PengXing_Huang/article/details/136460133#:~:text=%E5%BD%93%E4%BD%A0%E7%9C%8B%E5%88%B0%60npm%20i  
2.Web3.providers.HttpProvider("http://121.248.49.48:8545"); 切换成本地地址，用ipconfig查看  
3.运行chain33：chain33.exe -f chain33.toml；查询链信息：chain33-cli net peer info  
4.之后就能runcode了。可以跑的有online-map-demo和local-db（后者需要安装的npm install -g nedb） 

------
11.4  
中间的日志由于强行覆写丢掉了，不过没事，本项目已经接近尾声，现在所有功能均已经测试通过  
由于时间紧迫，UE侧和CA侧各做了一个监听，这个监听只有在连接到SEU局域网的时候能和局域网内的用户通信，否则就需要配置端口  
基本逻辑：   
## 前置部署  
```
./chain33.exe -f chain33.toml   //启动
./chain33-cli net peer info     //查状态和ip
```
新增了一些区块链钱包的额外步骤
```
//解锁钱包，如果没有钱包需要先创建钱包，bash命令如下：
.\chain33-cli seed generate -l 0
.\chain33-cli seed save -s '生产的助记词' -p 密码    //密码要有字母+数字，牢记，不然要干掉整个钱包
.\chain33-cli wallet unlock -p 密码 -t 0
//不解锁的话不能创建账户
```
本项目基于Openssl提供的密码学操作（js本身的密码学插件很难用）生成密钥，基于key生成证书，证书的认证过程完全在链上完成  
现在由于已经编译，不需要再安装nodejs，但是需要[openssl安装](https://slproweb.com/products/Win32OpenSSL.html)，点击下载，轻量版就能用，安装后将其/bin放到系统路径中（注意，必须要比其它包含openssl的路径前，不然会出现调用错误，也就是说这个路径要在path里的前几个，甚至第一个）  
```
openssl version  //cmd有结果才能执行openssl操作
```
  
## config文件配置
注意：需要按环境更改，这些默认的配置需要在所有实验步骤之前先同步到各个UE节点：  
```
{  
  "Blockchain": {  
    //区块链节点地址，也就是主机的地址，用.\chain33-cli net peer info可查询，也可以ipconfig   
      
    "providerUrl": "http://121.248.51.6:8545",     
    //创世地址，要保证这个地址里有gas   
      
    "account": "0xab7F5238cbEfB02062241cf979e4994b656FB944",     
    //创世地址的私钥，原则上每个UE节点需要有一个account，但是还要转账太麻烦了，就全部用创世地址顶一下  
      
     "privateKey": "0x73e66f099144f820753aa3a5e131785b528081da572e16339fcd02de05de719e"   
     },   
       
  "contract": {  
    //默认是这个，不用动   
    "abiPath": "./authentication.abi",             
      
    //同上   
    "bytecodePath": "./authentication.code",       
      
    //合约地址，执行DPKI-CA中的deploycontract函数会部署合约，这里填合约地址 ##待做成自动化的，但是对演示无益，所以暂时不做  
    "address": "0x99c7FDb06Bf5832Ef13dCA9aa67Da8EfBE2Cba35"    
  },  
    
  "Servernetwork": {
    //主机地址，能看得出来这是SEU局域网地址   
    "serverHost": "121.248.51.6",              
      
    //监听的端口，默认主机是12349端口，UE是12348   
    "serverPort": 12349                            
  }  
}
```
  
然后执行 ./exe即可完成操作，exe文件可以不用放在工程目录下，有DPKI-config.json，两个合约相关的文件（authentication.abi和authentication.code，这个是编译的bug，需要修正）即可  
所以，CA和UE可以完成局域网（校园网）里的证书操作，一个当CA两个当UE即可完成最简单的环境部署。当然，本地也可以完成这一操作  
CA侧包含Server-CA和DPKI-CA两个可执行，UE侧包含Server-UE和DPKI-UE两个可执行  

## 实验流程：  
1、打开两端的所有监听：(两端)  
```
./Server-CA  
./Server-UE
```
  
2.初始化root证书并上链：（CA端） 
```
./DPKI-CA initial -ca_name string -ca_label string  
//一般来说这两个是相同的，label用于在链上注册时的key，value则是证书信息等，所以一般来说label和name需要保持一致，但是由于CA特殊性预留了自定义label的功能
```
  
3.UE发起CSR：（UE端 to CA端）  
```
./DPKI-UE request -ue_name string                  
//这里ue自己无权设置label，发送的root地址写在DPKI-config文件里，同时也是单节点区块链的主机，所以config需要先按照环境修改，再同步给UE节点，UE节点至少需要默认状态下的字段；这一步同时还有一个作用，CA的监听在听到csr后会将该地址以ca name记录在config中，也就是回信的地址和端口
```
  
4. CA签署证书： （CA端 to UE端）
```
./DPKI-CA register -ca_name string -ue_name string   
//用ca签署ue证书（对应的csr），并将证书及一系列信息（包括validity，公钥对应的以太坊地址（作为后续开发的用户账户地址以及challenge的秘密））上链，以ca name-json（证书信息）的mapping存储在合约里。需注意，register功能不允许label，也就是ca name重复，即使在本地把证书库删了，链上还是不会通过，所以要新建一个仓库就需要重新部署一个合约，用新的地址来做
```
  
5. CA更新证书    （CA端 to UE端）
```
./DPKI-CA update -ca_name string -ue_name string     
//逻辑和register相似，不同的是，update允许覆写已存在label的证书及信息，一般来说是用于更新时间戳（要体现这点需要把config里证书的有效期压缩到1-2min，尤老师的项目），##待开发，UE侧暂时不会收到更新后的证书，会出问题（但也可以通过只更新链上validity的方式糊弄过去，再说）
```
  
6. CA撤销证书     （CA端 to UE端）
```
./DPKI-CA revoke -ue_name string                    
//最直观的撤销，可以明显看出证书在验证时失效      ##待开发，UE侧暂时不会收到通知，但是不会影响其他逻辑
```
  
7. UE更新地址列表   （CA端 to UE端）
```
./DPKI-UE updatelist                                 
//更新ue本地的DPKI-config，不然找不到了        ##这个功能还需要很多进一步开发。比如，这个玩意事实上应该放链上，其次，它应该还要带一个标识，写上证书目前的状态。但是现在暂时先这样，暂时只作为一个从CA获取其他UE地址的途径
```
  
8. UE间认证        （UE端1 to UE端2）
```
./DPKI-UE authenticationreq -ue_name string -target string         
//ue name是为了区分万一本地有很多个证书，target一样，是对方的ue名，其实也就是config里的那个名称对应的地址；认证逻辑如下  
//UE1生成一个签名，由其私钥为其以太坊地址签名，加上证书原文，send给ue2  
//UE2的监听收到消息  
//UE2把这些信息传到合约  
//合约帮助验证：1、证书原文和证书库里的是否匹配（哈希是否匹配）2、证书时间戳（链上的状态）是否超出了区块链当前的时间戳 3、证书签名恢复地址是否匹配（也就是验证签名），4、证书是否有效（有无被撤销），这四个是有先后顺序的，如果未通过，报错只报最后一个（中文报错，重要级最高）  
//如果全部通过，UE1客户端和UE2监听均可收到认证通过的消息
```
                                                                

                                                              
                                                                
