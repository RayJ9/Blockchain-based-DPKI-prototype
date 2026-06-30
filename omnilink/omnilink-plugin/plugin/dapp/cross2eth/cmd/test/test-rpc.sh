#!/usr/bin/env bash
#shellcheck disable=SC2128
#shellcheck source=/dev/null
set -x
source ../dapp-test-common.sh

MAIN_HTTP=""

function rpc_test() {
    omnilink_RpcTestBegin cross2eth
    MAIN_HTTP="$1"
    echo "main_ip=$MAIN_HTTP"

    omnilink_RpcTestRst cross2eth "$CASE_ERR"
}

omnilink_debug_function rpc_test "$1" "$2"
