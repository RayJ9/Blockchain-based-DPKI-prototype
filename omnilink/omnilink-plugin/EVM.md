
# Omnilink 中使用 EVM 开发的要点

## Omnilink 对 EVM 的兼容

1. Omnilink 分析输入的交易，如果是 EVM 交易，则递交给改造并集成到 Omnilink 中的 EVM 处理，并将结果写入 KV 数据库，因此，Omnilink完全兼容EVM。
2. Omnilink 平行链（Layer-2）也支持 EVM。
3. 编写 EVM 合约推荐使用 Solidity 0.6.10 版本，Abigen 版本推荐使用 1.10.7-stable。
4. 支持以太坊 go-sdk 工具链（该项将在后面详细介绍）。

## 合约编写与调试

1. 与其他支持 EVM 链的开发流程类似，编写 `.sol` 合约可使用任意编辑器。
2. **简单合约调试**：推荐使用 [Remix](https://remix.ethereum.org/)。
3. **复杂合约调试**：推荐使用 [Hardhat](https://hardhat.org/)。

## SDK 的使用与业务集成

1. Omnilink 支持以太坊的 go-sdk 工具链，这意味着不只是合约开发，业务集成也完全与以太坊兼容。
2. 使用 go-sdk 可以方便地部署合约以及进行调用。

### 基本步骤如下：

1. **使用 `solc` 工具进行编译：**
    ```bash
    ./solc-0.6.10 --bin --abi -o ./ ./test.sol --overwrite
    ```

2. **使用 `abigen` 工具生成相应的 Go 语言文件：**
    ```bash
    ./abigen --bin ./test.bin --abi ./test.abi --pkg test --type test --out ./test.go
    ```

3. 将生成的 Go 语言文件复制到相应文件夹，后续可以直接调用。

### 部署与调用合约方法示例

1. **生成 Client**  

    ```go
    Omnilink 默认监听 8545 端口（与以太坊相同，可通过配置文件修改）：
    client, err := ethclient.Dial(ClientUrl)
    ```

2. **部署合约**
    ```go
    contractAddress = test.DeployTest(client.GetTransactOpts(), client.Client)
    ```

3. **构建 Session**
    ```go
    testSession = test.NewTest(contractAddress, client.Client)
    ```

4. **调用方法**  
    ```go
    假设 Test 合约有一个 `Set` 方法：
    testSession.Set(1)
    ```
5. **实际代码以及业务集成示例**
    ```
    ssh://git@code.corp.bcollie.net/source/tip.git，该代码仓库中有较多使用Go-SDK的例子
    ```
