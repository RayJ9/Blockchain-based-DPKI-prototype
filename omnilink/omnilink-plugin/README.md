# OmniLink Chain Plugin

## Omnilink由Base和Plugin两部分组成，使用不同的代码路径分别进行管理

### Base
```
具体参照Base代码仓库的Readme
```

### Plugin

#### 编译代码
```
1. 下载omnilink-plugin与omnilink-base到同一代码路径下,code.corp.bcollie.net/omnilink
2. 进入到omnilink-plugin路径
3. make

注意：请使用go 1.20版本
```

#### 本地运行
```
编译后在build路径下产生两个可执行文件omnilink以及omnilink-cli，本地调试以omnilink.solo.toml为配置文件运行, ./omnilink -f omnilink.solo.toml
```

#### 命令行使用
```
使用命令行转账是初次体验各个区块链的首选，以下是一个完整的示例
1. ./omnilink-cli seed save -s "final trap pause comfort banana shoe ahead truck salon intact video excuse quote leave flat" -p omnilink123
2. ./omnilink-cli wallet unlock -p omnilink123
3. ./omnilink-cli coins transfer -a 600 -t 0x49f90294233c864952cc90b3e00b25a3c3bc3ce9,产生data bytes xxxx
4. ./omnilink-cli wallet sign -k 041db3bbab39031b78f7e0032548cfcaf4c457c80ff924b8a0a355193a732e0e -p 2 -d xxxx, 产生签名后的数据 yyyy
5. ./omnilink-cli wallet send -d yyyy

注意：助记词并不重要，直接使用示例数据即可，第一次初始化Wallet必须使用助记词才能产生钱包密码，但后续再进行操作，不用重复第1步，在第4步签名时使用了genesis address对应的私钥
```

#### KV合约开发
```
Omnilink支持两类智能合约，EVM合约以及Golang原生合约，实际上Golang合约属于预编译合约，它是在编译阶段就确定的合约逻辑，采用自定义KV数据的方式最大化灵活程序设计。

注意：KV合约编写采用protobuf定义数据，请首先确保工具链正确安装，包括protoc(推荐版本，libprotoc 3.0.0)，protoc-gen-go。
```

### 代码提交 - Arcanist 安装

安装Arcanist
```
git clone https://github.com/phacility/arcanist.git $HOME/.local/
echo "export PATH=$HOME/.local/arcanist/bin:$PATH" >> $HOME/.bashrc
source $HOME/.bashrc

可以使用arc help测试是否安装成功
注：如果缺少PHP，可以安装PHP7.4及PHP7.4curl
首次运行

cd omnilink-plugin
arc install-certificate

根据指示粘贴对应的API
```

关于提交Diff

```
创建Diff
arc diff --create

更新Diff
arc diff --update <DIFF_ID>

提交代码(需要等待review)
arc land

```

