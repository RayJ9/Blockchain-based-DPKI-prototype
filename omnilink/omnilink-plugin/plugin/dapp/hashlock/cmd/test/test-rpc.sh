#!/usr/bin/env bash
# shellcheck disable=SC2128
# shellcheck source=/dev/null
set -e
set -o pipefail

MAIN_HTTP=""

addr_A=19vpbRuz2XtKopQS2ruiVuVZeRdLd5n4t3
addr_B=1FcofeCgU1KYbB8dSa7cV2wjAF2RpMuUQD
source ../dapp-test-common.sh

hashlock_lock() {
    local secret=$1
    tx=$(curl -ksd '{"method":"Omnilink.CreateTransaction","params":[{"execer":"hashlock","actionName":"HashlockLock", "payload":{"secret":"'"${secret}"'","amount":1000000000, "time":75,"toAddr":"'"${addr_B}"'", "returnAddr":"'"${addr_A}"'","fee":100000000}}]}' ${MAIN_HTTP} | jq -r ".result")
    omnilink_SignAndSendTxWait "$tx" "0x1089b7f980fc467f029b7ae301249b36e3b582c911b1af1a24616c83b3563dcb" ${MAIN_HTTP} "$FUNCNAME"
}

hashlock_send() {
    local secret=$1
    tx=$(curl -ksd '{"method":"Omnilink.CreateTransaction","params":[{"execer":"hashlock","actionName":"HashlockSend", "payload":{"secret":"'"${secret}"'","fee":100000000}}]}' ${MAIN_HTTP} | jq -r ".result")
    omnilink_SignAndSendTxWait "$tx" "0xb76a398c3901dfe5c7335525da88fda4df24c11ad11af4332f00c0953cc2910f" ${MAIN_HTTP} "$FUNCNAME"
}

hashlock_unlock() {
    local secret=$1
    tx=$(curl -ksd '{"method":"Omnilink.CreateTransaction","params":[{"execer":"hashlock","actionName":"HashlockUnlock", "payload":{"secret":"'"${secret}"'","fee":100000000}}]}' ${MAIN_HTTP} | jq -r ".result")
    omnilink_SignAndSendTxWait "$tx" "0x1089b7f980fc467f029b7ae301249b36e3b582c911b1af1a24616c83b3563dcb" ${MAIN_HTTP} "$FUNCNAME"
}

init() {
    ispara=$(echo '"'"${MAIN_HTTP}"'"' | jq '.|contains("8901")')
    echo "ipara=$ispara"
    if [ "$ispara" == true ]; then
        hashlock_addr=$(curl -ksd '{"method":"Omnilink.ConvertExectoAddr","params":[{"execname":"user.p.para.hashlock"}]}' ${MAIN_HTTP} | jq -r ".result")
    else
        hashlock_addr=$(curl -ksd '{"method":"Omnilink.ConvertExectoAddr","params":[{"execname":"hashlock"}]}' ${MAIN_HTTP} | jq -r ".result")
    fi

    local main_ip=${MAIN_HTTP//8901/8801}
    omnilink_ImportPrivkey "0x1089b7f980fc467f029b7ae301249b36e3b582c911b1af1a24616c83b3563dcb" "19vpbRuz2XtKopQS2ruiVuVZeRdLd5n4t3" "hashlock1" "${main_ip}"
    omnilink_ImportPrivkey "0xb76a398c3901dfe5c7335525da88fda4df24c11ad11af4332f00c0953cc2910f" "1FcofeCgU1KYbB8dSa7cV2wjAF2RpMuUQD" "hashlock2" "$main_ip"

    local hashlock1="19vpbRuz2XtKopQS2ruiVuVZeRdLd5n4t3"
    local hashlock2="1FcofeCgU1KYbB8dSa7cV2wjAF2RpMuUQD"

    if [ "$ispara" == false ]; then
        omnilink_applyCoins "$hashlock1" 12000000000 "${main_ip}"
        omnilink_QueryBalance "${hashlock1}" "$main_ip"

        omnilink_applyCoins "$hashlock2" 12000000000 "${main_ip}"
        omnilink_QueryBalance "${hashlock2}" "$main_ip"
    else
        # tx fee
        omnilink_applyCoins "$hashlock1" 1000000000 "${main_ip}"
        omnilink_QueryBalance "${hashlock1}" "$main_ip"

        omnilink_applyCoins "$hashlock2" 1000000000 "${main_ip}"
        omnilink_QueryBalance "${hashlock2}" "$main_ip"
        local para_ip="${MAIN_HTTP}"
        #para chain import pri key
        omnilink_ImportPrivkey "0x1089b7f980fc467f029b7ae301249b36e3b582c911b1af1a24616c83b3563dcb" "19vpbRuz2XtKopQS2ruiVuVZeRdLd5n4t3" "hashlock1" "$para_ip"
        omnilink_ImportPrivkey "0xb76a398c3901dfe5c7335525da88fda4df24c11ad11af4332f00c0953cc2910f" "1FcofeCgU1KYbB8dSa7cV2wjAF2RpMuUQD" "hashlock2" "$para_ip"

        omnilink_applyCoins "$hashlock1" 12000000000 "${para_ip}"
        omnilink_QueryBalance "${hashlock1}" "$para_ip"
        omnilink_applyCoins "$hashlock2" 12000000000 "${para_ip}"
        omnilink_QueryBalance "${hashlock2}" "$para_ip"
    fi

    omnilink_SendToAddress "$hashlock1" "$hashlock_addr" 10000000000 ${MAIN_HTTP}
    omnilink_QueryExecBalance "${hashlock1}" "hashlock" "$MAIN_HTTP"
    omnilink_SendToAddress "$hashlock2" "$hashlock_addr" 10000000000 ${MAIN_HTTP}
    omnilink_QueryExecBalance "${hashlock2}" "hashlock" "$MAIN_HTTP"

    omnilink_BlockWait 1 "${MAIN_HTTP}"
}

function run_test() {
    omnilink_QueryBalance "$addr_A" "${MAIN_HTTP}"
    omnilink_QueryBalance "$addr_B" "${MAIN_HTTP}"
    hashlock_lock "abc"
    omnilink_QueryBalance "$addr_A" "${MAIN_HTTP}"
    hashlock_send "abc"
    omnilink_QueryBalance "$addr_B" "${MAIN_HTTP}"
    hashlock_unlock "abc"
    hashlock_lock "aef"
    omnilink_QueryBalance "$addr_A" "${MAIN_HTTP}"
    sleep 5
    hashlock_unlock "aef"
    omnilink_BlockWait 1 ${MAIN_HTTP}
    omnilink_QueryBalance "$addr_A" "${MAIN_HTTP}"
}

function main() {
    omnilink_RpcTestBegin hashlock
    MAIN_HTTP="$1"
    echo "ip=$MAIN_HTTP"

    init
    run_test
    omnilink_RpcTestRst hashlock "$CASE_ERR"
}

omnilink_debug_function main "$1"
