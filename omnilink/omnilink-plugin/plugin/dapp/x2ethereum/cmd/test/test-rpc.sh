#!/usr/bin/env bash
##shellcheck disable=SC2128
##shellcheck source=/dev/null
#set -x
#source ../dapp-test-common.sh
#source "../x2ethereum/publicTest.sh"
#
#sendAddress="12qyocayNF7Lv6C9qW4avxs2E7U41fKSfv"
#sendPriKey="0x4257d8692ef7fe13c68b65d6a52f03933db2fa5ce8faf210b5b8b80c721ced01"
#MAIN_HTTP=""
#omnilinkSenderAddr="14KEKbYtKKQm4wMthSK9J4La4nAiidGozt"
## validatorsAddr=["0x92c8b16afd6d423652559c6e266cbe1c29bfd84f", "0x0df9a824699bc5878232c9e612fe1a5346a5a368", "0xcb074cb21cdddf3ce9c3c0a7ac4497d633c9d9f1", "0xd9dab021e74ecf475788ed7b61356056b2095830"]
#ethValidatorAddrKeyA="3fa21584ae2e4fd74db9b58e2386f5481607dfa4d7ba0617aaa7858e5025dc1e"
#ethValidatorAddrKeyB="a5f3063552f4483cfc20ac4f40f45b798791379862219de9e915c64722c1d400"
#ethValidatorAddrKeyC="bbf5e65539e9af0eb0cfac30bad475111054b09c11d668fc0731d54ea777471e"
#ethValidatorAddrKeyD="c9fa31d7984edf81b8ef3b40c761f1847f6fcd5711ab2462da97dc458f1f896b"
## 新增地址 omnilink 需要导入地址 转入 10 bty当收费费
#omnilinkValidator1="1H4zzzQEQQR2FxXwppiMRXcvqLvqzxK2nv"
#omnilinkValidator2="1Nq5AhTgVNvYaWQqih8ZQQEaRk3CFhTDHp"
#omnilinkValidator3="16nmxjF58z5oKK9m44cGy241zMSJWPN1Ty"
#omnilinkValidator4="182nAEMxF1JWWxEWdu4jvd68aZhQumS97H"
#omnilinkValidatorKey1="0x260124d9c619b0088241ffe2f1d7dc56b0b6100c88c342040387cd62b8ba35a3"
#omnilinkValidatorKey2="0x7812f8c688048943f1c168f8f2f76f44912de1f0ff8b12358b213118081869b2"
#omnilinkValidatorKey3="0xd44c8f3d8cac5d9c7fef7b0a0bf7be0909372ec6368064f742193de0bddeb2d1"
#omnilinkValidatorKey4="0xaad36689ca332026d4a4ceee62c8a91bac7bc100906b25a181a7f28b8552b53e"
#ethReceiverAddr1="0xa4ea64a583f6e51c3799335b28a8f0529570a635"
#ethReceiverAddrKey1="355b876d7cbcb930d5dfab767f66336ce327e082cbaa1877210c1bae89b1df71"
#ethReceiverAddr2="0x0c05ba5c230fdaa503b53702af1962e08d0c60bf"
##ethReceiverAddrKey2="9dc6df3a8ab139a54d8a984f54958ae0661f880229bf3bdbb886b87d58b56a08"
#maturityDegree=5
##portRelayer=19999
#ethUrl=""
#
#CLIA_HTTP=""
#CLIB_HTTP=""
#CLIC_HTTP=""
#CLID_HTTP=""
#
## $1 sendAddress, $2 balance
#function queryExecBalance() {
#    local resp=""
#    omnilink_QueryExecBalance "${1}" "x2ethereum" "$MAIN_HTTP"
#    # shellcheck disable=SC2155
#    local balance=$(echo "$resp" | jq -r ".result" | jq ".[].balance")
#    if [ "${balance}" != "${2}" ]; then
#        echo_rst "queryExecBalance" "1" "${balance} != ${2}"
#    fi
#}
#
## $1 omnilinkAddress, $2 balance
#function queryOmnilinkBalance() {
#    local resp=""
#    omnilink_QueryBalance "${1}" "${MAIN_HTTP}"
#    # shellcheck disable=SC2155
#    local balance=$(echo $resp | jq -r ".result.execAccount" | jq ".[].account.balance")
#    if [ "${balance}" != "${2}" ]; then
#        echo_rst "queryOmnilinkBalance" "1" "${balance} != ${2}"
#    fi
#}
#
## $1 req , $2 balance
#function queryRelayerBalance() {
#    omnilink_Http "${1}" "${CLIA_HTTP}" '(.error|not) and (.result != null)' "GetBalance" ".result.balance"
#    if [ "${RETURN_RESP}" != "${2}" ]; then
#        echo_rst "queryRelayerBalance" "1" "${RETURN_RESP} != ${2}"
#        copyErrLogs
#    fi
#}
#
## $1 req , $2 balance
#function queryOmnilinkX2ethBalance() {
#    omnilink_Http "${req}" ${MAIN_HTTP} '(.error|not) and (.result != null)' "GetBalance" ".result"
#    # shellcheck disable=SC2155
#    local balance=$(echo "${RETURN_RESP}" | jq -r ".res" | jq ".[].balance" | sed 's/\"//g')
#    if [ "${balance}" != "${2}" ]; then
#        echo_rst "queryOmnilinkX2ethBalance" "1" "${balance} != ${2}"
#    fi
#}
#
#function start_ebrelayerA() {
#    docker cp "./x2ethereum/relayer.toml" "${dockerNamePrefix}_ebrelayera_rpc_1":/root/relayer.toml
#    start_docker_ebrelayer "${dockerNamePrefix}_ebrelayera_rpc_1" "/root/ebrelayer" "./x2ethereum/ebrelayera.log"
#    sleep 5
#}
#
#function StartRelayerAndDeploy() {
#    echo -e "${GRE}=========== $FUNCNAME begin ===========${NOC}"
#
#    cp ../x2ethereum/* ./x2ethereum/
#    for dockerName in ganachetest ebrelayera ebrelayerb ebrelayerc ebrelayerd; do
#        line=$(delete_line_show "./x2ethereum/docker-compose-x2ethereum.yml" "${dockerName}:")
#        sed -i ''"${line}"' a \ \ '${dockerName}'_rpc:' "./x2ethereum/docker-compose-x2ethereum.yml"
#    done
#
#    docker-compose -f ./x2ethereum/docker-compose-x2ethereum.yml up --build -d
#    sleep 5
#
#    # change EthProvider url
#    dockerAddr=$(get_docker_addr "${dockerNamePrefix}_ganachetest_rpc_1")
#    ethUrl="http://${dockerAddr}:8545"
#
#    # 修改 relayer.toml 配置文件
#    updata_relayer_a_toml "${dockerAddr}" "${dockerNamePrefix}_ebrelayera_rpc_1" "./x2ethereum/relayer.toml"
#
#    line=$(delete_line_show "./x2ethereum/relayer.toml" "localhost:9901")
#    sed -i ''"${line}"' a JrpcBindAddr=":9901"' "./x2ethereum/relayer.toml"
#    # start ebrelayer A
#    start_ebrelayerA
#
#    ebrelayeraRpcHost=$(get_docker_addr "${dockerNamePrefix}_ebrelayera_rpc_1")
#    if [[ ${ebrelayeraRpcHost} == "" ]]; then
#        echo -e "${RED}ebrelayeraRpcHost a is empty${NOC}"
#    fi
#    CLIA_HTTP="http://${ebrelayeraRpcHost}:9901"
#
#    # 部署合约
#    InitAndDeploy
#
#    # 获取 BridgeRegistry 地址
#    local req='{"method":"Manager.ShowBridgeRegistryAddr","params":[{}]}'
#    omnilink_Http "$req" "${CLIA_HTTP}" '(.error|not) and (.result != null)' "$FUNCNAME" ".result.addr"
#    local BridgeRegistry="$RETURN_RESP"
#
#    # kill ebrelayer A
#    kill_docker_ebrelayer "${dockerNamePrefix}_ebrelayera_rpc_1"
#    sleep 1
#
#    # 修改 relayer.toml 配置文件
#    updata_relayer_toml "${BridgeRegistry}" ${maturityDegree} "./x2ethereum/relayer.toml"
#    # 重启
#    start_ebrelayerA
#
#    # start ebrelayer B C D
#    for name in b c d; do
#        local file="./x2ethereum/relayer$name.toml"
#        cp './x2ethereum/relayer.toml' "${file}"
#
#        # 删除配置文件中不需要的字段
#        for deleteName in "deployerPrivateKey" "operatorAddr" "validatorsAddr" "initPowers" "deployerPrivateKey" "deploy"; do
#            delete_line "${file}" "${deleteName}"
#        done
#
#        sed -i 's/x2ethereum/x2ethereum'${name}'/g' "${file}"
#
#        pushHost=$(get_docker_addr "${dockerNamePrefix}_ebrelayer${name}_rpc_1")
#        line=$(delete_line_show "${file}" "pushHost")
#        sed -i ''"${line}"' a pushHost="http://'"${pushHost}"':20000"' "${file}"
#
#        line=$(delete_line_show "${file}" "pushBind")
#        sed -i ''"${line}"' a pushBind="'"${pushHost}"':20000"' "${file}"
#
#        docker cp "${file}" "${dockerNamePrefix}_ebrelayer${name}_rpc_1":/root/relayer.toml
#        start_docker_ebrelayer "${dockerNamePrefix}_ebrelayer${name}_rpc_1" "/root/ebrelayer" "./x2ethereum/ebrelayer${name}.log"
#    done
#    sleep 5
#
#    ebrelayeraRpcHost=$(get_docker_addr "${dockerNamePrefix}_ebrelayera_rpc_1")
#    CLIA_HTTP="http://${ebrelayeraRpcHost}:9901"
#    ebrelayeraRpcHost=$(get_docker_addr "${dockerNamePrefix}_ebrelayerb_rpc_1")
#    CLIB_HTTP="http://${ebrelayeraRpcHost}:9901"
#    ebrelayeraRpcHost=$(get_docker_addr "${dockerNamePrefix}_ebrelayerc_rpc_1")
#    CLIC_HTTP="http://${ebrelayeraRpcHost}:9901"
#    ebrelayeraRpcHost=$(get_docker_addr "${dockerNamePrefix}_ebrelayerd_rpc_1")
#    CLID_HTTP="http://${ebrelayeraRpcHost}:9901"
#
#    docker ps -a
#
#    echo -e "${GRE}=========== $FUNCNAME end ===========${NOC}"
#}
#
#function InitAndDeploy() {
#    echo -e "${GRE}=========== $FUNCNAME begin ===========${NOC}"
#    local req='{"method":"Manager.SetPassphase","params":[{"Passphase":"123456hzj"}]}'
#    omnilink_Http "$req" "${CLIA_HTTP}" '(.error|not) and (.result != null)' "SetPassphase" ".result"
#
#    local req='{"method":"Manager.Unlock","params":["123456hzj"]}'
#    omnilink_Http "$req" "${CLIA_HTTP}" '(.error|not) and (.result != null)' "Unlock" ".result"
#
#    local req='{"method":"Manager.DeployContrcts","params":[{}]}'
#    omnilink_Http "$req" "${CLIA_HTTP}" '(.error|not) and (.result != null)' "$FUNCNAME" ".result"
#    echo -e "${GRE}=========== $FUNCNAME end ===========${NOC}"
#}
#
## chian33 添加验证着及权重
#function InitOmnilinkVilators() {
#    echo -e "${GRE}=========== $FUNCNAME begin ===========${NOC}"
#    # 导入 omnilinkValidators 私钥生成地址
#    omnilink_ImportPrivkey "${omnilinkValidatorKey1}" "${omnilinkValidator1}" "tokenAddr" "${MAIN_HTTP}"
#    omnilink_ImportPrivkey "${omnilinkValidatorKey2}" "${omnilinkValidator2}" "tokenAddr" "${MAIN_HTTP}"
#    omnilink_ImportPrivkey "${omnilinkValidatorKey3}" "${omnilinkValidator3}" "tokenAddr" "${MAIN_HTTP}"
#    omnilink_ImportPrivkey "${omnilinkValidatorKey4}" "${omnilinkValidator4}" "tokenAddr" "${MAIN_HTTP}"
#
#    # SetConsensusThreshold
#    tx=$(curl -ksd '{"method":"Omnilink.CreateTransaction","params":[{"execer":"x2ethereum","actionName":"SetConsensusThreshold","payload":{"consensusThreshold":"80"}}]}' ${MAIN_HTTP} | jq -r ".result")
#    omnilink_SignAndSendTxWait "$tx" "$sendPriKey" ${MAIN_HTTP} "SetConsensusThreshold"
#
#    # add a validator
#    tx=$(curl -ksd '{"method":"Omnilink.CreateTransaction","params":[{"execer":"x2ethereum","actionName":"AddValidator","payload":{"address":"'${omnilinkValidator1}'","power":"25"}}]}' ${MAIN_HTTP} | jq -r ".result")
#    omnilink_SignAndSendTxWait "$tx" "$sendPriKey" ${MAIN_HTTP} "AddValidator"
#    tx=$(curl -ksd '{"method":"Omnilink.CreateTransaction","params":[{"execer":"x2ethereum","actionName":"AddValidator","payload":{"address":"'${omnilinkValidator2}'","power":"25"}}]}' ${MAIN_HTTP} | jq -r ".result")
#    omnilink_SignAndSendTxWait "$tx" "$sendPriKey" ${MAIN_HTTP} "AddValidator"
#    tx=$(curl -ksd '{"method":"Omnilink.CreateTransaction","params":[{"execer":"x2ethereum","actionName":"AddValidator","payload":{"address":"'${omnilinkValidator3}'","power":"25"}}]}' ${MAIN_HTTP} | jq -r ".result")
#    omnilink_SignAndSendTxWait "$tx" "$sendPriKey" ${MAIN_HTTP} "AddValidator"
#    tx=$(curl -ksd '{"method":"Omnilink.CreateTransaction","params":[{"execer":"x2ethereum","actionName":"AddValidator","payload":{"address":"'${omnilinkValidator4}'","power":"25"}}]}' ${MAIN_HTTP} | jq -r ".result")
#    omnilink_SignAndSendTxWait "$tx" "$sendPriKey" ${MAIN_HTTP} "AddValidator"
#
#    # query Validators
#    omnilink_Http '{"method":"Omnilink.Query","params":[{"execer":"x2ethereum","funcName":"GetTotalPower","payload":{}}]}' ${MAIN_HTTP} '(.error|not) and (.result != null)' "GetTotalPower" ".result.totalPower"
#    if [ "${RETURN_RESP}" != "100" ]; then
#        echo -e "${RED}=========== GetTotalPower err: TotalPower = $RETURN_RESP ===========${NOC}"
#    fi
#
#    # cions 转帐到 x2ethereum 合约地址
#    x2eth_addr=$(curl -ksd '{"method":"Omnilink.ConvertExectoAddr","params":[{"execname":"x2ethereum"}]}' ${MAIN_HTTP} | jq -r ".result")
#    omnilink_SendToAddress "${sendAddress}" "${x2eth_addr}" 20000000000 "${MAIN_HTTP}"
#    queryExecBalance "${sendAddress}" "20000000000"
#
#    # omnilinkValidator 要有手续费
#    omnilink_applyCoins "${omnilinkValidator1}" 1000000000 "${MAIN_HTTP}"
#    queryOmnilinkBalance "${omnilinkValidator1}" "1000000000"
#    omnilink_applyCoins "${omnilinkValidator2}" 1000000000 "${MAIN_HTTP}"
#    queryOmnilinkBalance "${omnilinkValidator2}" "1000000000"
#    omnilink_applyCoins "${omnilinkValidator3}" 1000000000 "${MAIN_HTTP}"
#    queryOmnilinkBalance "${omnilinkValidator3}" "1000000000"
#    omnilink_applyCoins "${omnilinkValidator4}" 1000000000 "${MAIN_HTTP}"
#    queryOmnilinkBalance "${omnilinkValidator4}" "1000000000"
#    echo -e "${GRE}=========== $FUNCNAME end ===========${NOC}"
#}
#
#function EthImportKey() {
#    echo -e "${GRE}=========== $FUNCNAME begin ===========${NOC}"
#
#    # 解锁
#    local req='{"method":"Manager.SetPassphase","params":[{"Passphase":"123456hzj"}]}'
#    omnilink_Http "$req" "${CLIB_HTTP}" '(.error|not) and (.result != null)' "SetPassphase" ".result"
#    omnilink_Http "$req" "${CLIC_HTTP}" '(.error|not) and (.result != null)' "SetPassphase" ".result"
#    omnilink_Http "$req" "${CLID_HTTP}" '(.error|not) and (.result != null)' "SetPassphase" ".result"
#    req='{"method":"Manager.Unlock","params":["123456hzj"]}'
#    omnilink_Http "$req" "${CLIA_HTTP}" '(.error|not) and (.result != null)' "Unlock" ".result"
#    omnilink_Http "$req" "${CLIB_HTTP}" '(.error|not) and (.result != null)' "Unlock" ".result"
#    omnilink_Http "$req" "${CLIC_HTTP}" '(.error|not) and (.result != null)' "Unlock" ".result"
#    omnilink_Http "$req" "${CLID_HTTP}" '(.error|not) and (.result != null)' "Unlock" ".result"
#
#    req='{"method":"Manager.ImportOmnilinkPrivateKey4EthRelayer","params":["'${omnilinkValidatorKey1}'"]}'
#    omnilink_Http "$req" "${CLIA_HTTP}" '(.error|not) and (.result != null)' "ImportOmnilinkPrivateKey4EthRelayer" ".result"
#    req='{"method":"Manager.ImportOmnilinkPrivateKey4EthRelayer","params":["'${omnilinkValidatorKey2}'"]}'
#    omnilink_Http "$req" "${CLIB_HTTP}" '(.error|not) and (.result != null)' "ImportOmnilinkPrivateKey4EthRelayer" ".result"
#    req='{"method":"Manager.ImportOmnilinkPrivateKey4EthRelayer","params":["'${omnilinkValidatorKey3}'"]}'
#    omnilink_Http "$req" "${CLIC_HTTP}" '(.error|not) and (.result != null)' "ImportOmnilinkPrivateKey4EthRelayer" ".result"
#    req='{"method":"Manager.ImportOmnilinkPrivateKey4EthRelayer","params":["'${omnilinkValidatorKey4}'"]}'
#    omnilink_Http "$req" "${CLID_HTTP}" '(.error|not) and (.result != null)' "ImportOmnilinkPrivateKey4EthRelayer" ".result"
#
#    req='{"method":"Manager.ImportOmnilinkRelayerPrivateKey","params":[{"privateKey":"'${ethValidatorAddrKeyA}'"}]}'
#    omnilink_Http "$req" "${CLIA_HTTP}" '(.error|not) and (.result != null)' "ImportOmnilinkRelayerPrivateKey" ".result"
#    req='{"method":"Manager.ImportOmnilinkRelayerPrivateKey","params":[{"privateKey":"'${ethValidatorAddrKeyB}'"}]}'
#    omnilink_Http "$req" "${CLIB_HTTP}" '(.error|not) and (.result != null)' "ImportOmnilinkRelayerPrivateKey" ".result"
#    req='{"method":"Manager.ImportOmnilinkRelayerPrivateKey","params":[{"privateKey":"'${ethValidatorAddrKeyC}'"}]}'
#    omnilink_Http "$req" "${CLIC_HTTP}" '(.error|not) and (.result != null)' "ImportOmnilinkRelayerPrivateKey" ".result"
#    req='{"method":"Manager.ImportOmnilinkRelayerPrivateKey","params":[{"privateKey":"'${ethValidatorAddrKeyD}'"}]}'
#    omnilink_Http "$req" "${CLID_HTTP}" '(.error|not) and (.result != null)' "ImportOmnilinkRelayerPrivateKey" ".result"
#
#    echo -e "${GRE}=========== $FUNCNAME end ===========${NOC}"
#}
#
#function TestOmnilinkToEthAssets() {
#    echo -e "${GRE}=========== $FUNCNAME begin ===========${NOC}"
#    # token4omnilink 在 以太坊 上先有 bty
#    local req='{"method":"Manager.CreateBridgeToken","params":["coins.bty"]}'
#    omnilink_Http "$req" "${CLIA_HTTP}" '(.error|not) and (.result != null)' "CreateBridgeToken" ".result.addr"
#    tokenAddrBty=${RETURN_RESP}
#
#    req='{"method":"Manager.GetBalance","params":[{"owner":"'${ethReceiverAddr1}'","tokenAddr":"'${tokenAddrBty}'"}]}'
#    queryRelayerBalance "$req" "0"
#
#    # omnilink lock bty
#    #shellcheck disable=SC2086
#    tx=$(curl -ksd '{"method":"Omnilink.CreateTransaction","params":[{"execer":"x2ethereum","actionName":"OmnilinkToEthLock","payload":{"TokenContract":"'${tokenAddrBty}'","OmnilinkSender":"'${sendPriKey}'","EthereumReceiver":"'${ethReceiverAddr1}'","Amount":"500000000","IssuerDotSymbol":"coins.bty","Decimals":"8"}}]}' ${MAIN_HTTP} | jq -r ".result")
#    omnilink_SignAndSendTxWait "$tx" "$sendPriKey" ${MAIN_HTTP} "OmnilinkToEthLock"
#
#    queryExecBalance "${sendAddress}" "19500000000"
#
#    eth_block_wait $((maturityDegree + 2)) "${ethUrl}"
#
#    req='{"method":"Manager.GetBalance","params":[{"owner":"'${ethReceiverAddr1}'","tokenAddr":"'${tokenAddrBty}'"}]}'
#    queryRelayerBalance "$req" "5"
#
#    # eth burn
#    req='{"method":"Manager.Burn","params":[{"ownerKey":"'${ethReceiverAddrKey1}'","tokenAddr":"'${tokenAddrBty}'","omnilinkReceiver":"'${omnilinkSenderAddr}'","amount":"500000000"}]}'
#    omnilink_Http "$req" "${CLIA_HTTP}" '(.error|not) and (.result != null)' "Burn" ".result"
#
#    req='{"method":"Manager.GetBalance","params":[{"owner":"'${ethReceiverAddr1}'","tokenAddr":"'${tokenAddrBty}'"}]}'
#    queryRelayerBalance "$req" "0"
#
#    # eth 等待 10 个区块
#    eth_block_wait $((maturityDegree + 2)) "${ethUrl}"
#
#    queryExecBalance "${omnilinkSenderAddr}" "500000000"
#
#    echo -e "${GRE}=========== $FUNCNAME end ===========${NOC}"
#}
#
## eth to omnilink
## 在以太坊上锁定资产,然后在 omnilink 上铸币,针对 eth 资产
#function TestETH2OmnilinkAssets() {
#    echo -e "${GRE}=========== $FUNCNAME begin ===========${NOC}"
#    local req='{"method":"Manager.ShowBridgeBankAddr","params":[{}]}'
#    omnilink_Http "$req" "${CLIA_HTTP}" '(.error|not) and (.result != null)' "ShowBridgeBankAddr" ".result.addr"
#    bridgeBankAddr="${RETURN_RESP}"
#
#    req='{"method":"Manager.GetBalance","params":[{"owner":"'${bridgeBankAddr}'","tokenAddr":""}]}'
#    queryRelayerBalance "$req" "0"
#
#    # eth lock 0.1
#    req='{"method":"Manager.LockEthErc20Asset","params":[{"ownerKey":"'${ethReceiverAddrKey1}'","tokenAddr":"","amount":"100000000000000000","omnilinkReceiver":"'${sendAddress}'"}]}'
#    omnilink_Http "$req" "${CLIA_HTTP}" '(.error|not) and (.result != null)' "LockEthErc20Asset" ".result"
#
#    req='{"method":"Manager.GetBalance","params":[{"owner":"'${bridgeBankAddr}'","tokenAddr":""}]}'
#    queryRelayerBalance "$req" "0.1"
#
#    # eth 等待 10 个区块
#    eth_block_wait $((maturityDegree + 2)) "${ethUrl}"
#
#    req='{"method":"Omnilink.Query","params":[{"execer":"x2ethereum","funcName":"GetRelayerBalance","payload":{"tokenSymbol":"eth","address":"'${sendAddress}'","tokenAddr":"0x0000000000000000000000000000000000000000"}}]}'
#    queryOmnilinkX2ethBalance "${req}" "0.1"
#
#    req='{"method":"Manager.GetBalance","params":[{"owner":"'${ethReceiverAddr2}'","tokenAddr":""}]}'
#    omnilink_Http "${req}" "${CLIA_HTTP}" '(.error|not) and (.result != null)' "GetBalance" ".result.balance"
#    local balance=${RETURN_RESP}
#
#    #    burn 0.1
#    tx=$(curl -ksd '{"method":"Omnilink.CreateTransaction","params":[{"execer":"x2ethereum","actionName":"OmnilinkToEthBurn","payload":{"TokenContract":"0x0000000000000000000000000000000000000000","OmnilinkSender":"'${sendPriKey}'","EthereumReceiver":"'${ethReceiverAddr2}'","Amount":"10000000","IssuerDotSymbol":"eth","Decimals":"18"}}]}' ${MAIN_HTTP} | jq -r ".result")
#    omnilink_SignAndSendTxWait "$tx" "$sendPriKey" ${MAIN_HTTP} "OmnilinkToEthBurn"
#
#    req='{"method":"Omnilink.Query","params":[{"execer":"x2ethereum","funcName":"GetRelayerBalance","payload":{"tokenSymbol":"eth","address":"'${sendAddress}'","tokenAddr":"0x0000000000000000000000000000000000000000"}}]}'
#    queryOmnilinkX2ethBalance "${req}" "0"
#
#    eth_block_wait $((maturityDegree + 2)) "${ethUrl}"
#
#    req='{"method":"Manager.GetBalance","params":[{"owner":"'${bridgeBankAddr}'","tokenAddr":""}]}'
#    queryRelayerBalance "$req" "0"
#
#    req='{"method":"Manager.GetBalance","params":[{"owner":"'${ethReceiverAddr2}'","tokenAddr":""}]}'
#    #queryRelayerBalance "$req" "$(echo "${balance}+0.1" | bc)"
#    queryRelayerBalance "$req" "100.1"
#
#    echo -e "${GRE}=========== $FUNCNAME end ===========${NOC}"
#}
#
#function TestETH2OmnilinkErc20() {
#    echo -e "${GRE}=========== $FUNCNAME begin ===========${NOC}"
#    # token4erc20 在 omnilink 上先有 token,同时 mint
#    local req='{"method":"Manager.CreateERC20Token","params":["testc"]}'
#    omnilink_Http "$req" "${CLIA_HTTP}" '(.error|not) and (.result != null)' "CreateERC20Token" ".result.addr"
#    tokenAddr="${RETURN_RESP}"
#
#    # 先铸币 1000
#    req='{"method":"Manager.MintErc20","params":[{"owner":"'${ethReceiverAddr1}'","tokenAddr":"'${tokenAddr}'","amount":"100000000000"}]}'
#    omnilink_Http "$req" "${CLIA_HTTP}" '(.error|not) and (.result != null)' "MintErc20" ".result.addr"
#
#    req='{"method":"Manager.GetBalance","params":[{"owner":"'${ethReceiverAddr1}'","tokenAddr":"'${tokenAddr}'"}]}'
#    queryRelayerBalance "$req" "1000"
#
#    local req='{"method":"Manager.ShowBridgeBankAddr","params":[{}]}'
#    omnilink_Http "$req" "${CLIA_HTTP}" '(.error|not) and (.result != null)' "ShowBridgeBankAddr" ".result.addr"
#    bridgeBankAddr="${RETURN_RESP}"
#
#    req='{"method":"Manager.GetBalance","params":[{"owner":"'${bridgeBankAddr}'","tokenAddr":"'${tokenAddr}'"}]}'
#    queryRelayerBalance "$req" "0"
#
#    # lock 100
#    req='{"method":"Manager.LockEthErc20Asset","params":[{"ownerKey":"'${ethReceiverAddrKey1}'","tokenAddr":"'${tokenAddr}'","amount":"10000000000","omnilinkReceiver":"'${omnilinkValidator1}'"}]}'
#    omnilink_Http "$req" "${CLIA_HTTP}" '(.error|not) and (.result != null)' "LockEthErc20Asset" ".result"
#
#    req='{"method":"Manager.GetBalance","params":[{"owner":"'${ethReceiverAddr1}'","tokenAddr":"'${tokenAddr}'"}]}'
#    queryRelayerBalance "$req" "900"
#
#    req='{"method":"Manager.GetBalance","params":[{"owner":"'${bridgeBankAddr}'","tokenAddr":"'${tokenAddr}'"}]}'
#    queryRelayerBalance "$req" "100"
#
#    # eth 等待 10 个区块
#    eth_block_wait $((maturityDegree + 2)) "${ethUrl}"
#
#    req='{"method":"Omnilink.Query","params":[{"execer":"x2ethereum","funcName":"GetRelayerBalance","payload":{"tokenSymbol":"testc","address":"'${omnilinkValidator1}'","tokenAddr":"'${tokenAddr}'"}}]}'
#    queryOmnilinkX2ethBalance "${req}" "100"
#
#    # omnilink burn 100
#    #shellcheck disable=SC2086
#    tx=$(curl -ksd '{"method":"Omnilink.CreateTransaction","params":[{"execer":"x2ethereum","actionName":"OmnilinkToEthBurn","payload":{"TokenContract":"'${tokenAddr}'","OmnilinkSender":"'${omnilinkValidatorKey1}'","EthereumReceiver":"'${ethReceiverAddr2}'","Amount":"10000000000","IssuerDotSymbol":"testc","Decimals":"8"}}]}' ${MAIN_HTTP} | jq -r ".result")
#    omnilink_SignAndSendTxWait "$tx" "$omnilinkValidatorKey1" ${MAIN_HTTP} "OmnilinkToEthBurn"
#
#    req='{"method":"Omnilink.Query","params":[{"execer":"x2ethereum","funcName":"GetRelayerBalance","payload":{"tokenSymbol":"testc","address":"'${omnilinkValidator1}'","tokenAddr":"'${tokenAddr}'"}}]}'
#    queryOmnilinkX2ethBalance "${req}" "0"
#
#    eth_block_wait $((maturityDegree + 2)) "${ethUrl}"
#
#    req='{"method":"Manager.GetBalance","params":[{"owner":"'${ethReceiverAddr2}'","tokenAddr":"'${tokenAddr}'"}]}'
#    queryRelayerBalance "$req" "100"
#
#    req='{"method":"Manager.GetBalance","params":[{"owner":"'${bridgeBankAddr}'","tokenAddr":"'${tokenAddr}'"}]}'
#    queryRelayerBalance "$req" "0"
#
#    echo -e "${GRE}=========== $FUNCNAME end ===========${NOC}"
#}
#
function rpc_test() {
    #    set +e
    #    set -x
    omnilink_RpcTestBegin x2ethereum
    #    MAIN_HTTP="$1"
    #    dockerNamePrefix="$2"
    #    echo "main_ip=$MAIN_HTTP"
    #
    ##    ispara=$(echo '"'"${MAIN_HTTP}"'"' | jq '.|contains("8901")')
    ##    if [ "$ispara" == false ]; then
    ##        # init
    ##        StartRelayerAndDeploy
    ##        InitOmnilinkVilators
    ##        EthImportKey
    ##
    ##        # test
    ##        TestOmnilinkToEthAssets
    ##        TestETH2OmnilinkAssets
    ##        TestETH2OmnilinkErc20
    ##
    ##        copyErrLogs
    ##
    ##        docker-compose -f ./x2ethereum/docker-compose-x2ethereum.yml down
    ##    fi
    omnilink_RpcTestRst x2ethereum "$CASE_ERR"
}

#omnilink_debug_function rpc_test "$1" "$2"
