#!/usr/bin/env bash
#shellcheck disable=SC2128
#shellcheck source=/dev/null
set -x
source ../dapp-test-common.sh

MAIN_HTTP=""

function rpc_test() {
    omnilink_RpcTestBegin bridgevmxgo
    MAIN_HTTP="$1"
    echo "main_ip=$MAIN_HTTP"

    omnilink_RpcTestRst bridgevmxgo "$CASE_ERR"
}

omnilink_debug_function rpc_test "$1" "$2"
