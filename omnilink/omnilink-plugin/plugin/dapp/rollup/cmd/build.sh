#!/bin/bash
# 官方ci集成脚本
strpwd=$(pwd)
strcmd=${strpwd##*dapp/}
strapp=${strcmd%/cmd*}

OUT_DIR="${1}/$strapp"
#FLAG=$2

mkdir -p "${OUT_DIR}"
cp ./ci/* "${OUT_DIR}"

OMNILINK_PATH=$(go list -f "{{.Dir}}" code.corp.bcollie.net/omnilink/omnilink-base)
PLUGIN_PATH=$(go list -f "{{.Dir}}" code.corp.bcollie.net/omnilink/omnilink-plugin)
# copy omnilink toml

cp "${OMNILINK_PATH}/cmd/omnilink/omnilink.test.toml" "${OUT_DIR}"
cp "${PLUGIN_PATH}/omnilink.para.toml" "${OUT_DIR}"
