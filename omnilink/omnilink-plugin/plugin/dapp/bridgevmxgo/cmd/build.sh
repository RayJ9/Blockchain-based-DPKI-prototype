#!/usr/bin/env bash
# shellcheck disable=SC2086,1072

# 官方ci集成脚本
strpwd=$(pwd)
strcmd=${strpwd##*dapp/}
strapp=${strcmd%/cmd*}

SRC_EBCLI=code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/cross2eth/ebcli
SRC_EBRELAYER=code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/cross2eth/ebrelayer
SRC_BOSS4XCLI=code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/cross2eth/boss4x
SRC_EVMXGOBOSS4XCLI=code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/bridgevmxgo/boss4x

OUT_DIR="${1}/$strapp"
FLAG=$2

BuildTime=$(date +"%Y-%m-%d %H:%M:%S %A")
VERSION=$(git describe --tags || git rev-parse --short=8 HEAD)
GitCommit=$(git rev-parse HEAD)
BUILD_FLAGS='-X "code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/cross2eth/ebrelayer/version.GitCommit='${GitCommit}'" -X "code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/cross2eth/ebrelayer/version.BuildTime='${BuildTime}'" -X "code.corp.bcollie.net/omnilink/omnilink-plugin/version.Version='${VERSION}'"'

go build -ldflags "${BUILD_FLAGS}" -i ${FLAG} -v -o "${OUT_DIR}/ebrelayer" "${SRC_EBRELAYER}"
go build -ldflags "${BUILD_FLAGS}" -i ${FLAG} -v -o "${OUT_DIR}/ebcli_A" "${SRC_EBCLI}"
go build -i ${FLAG} -v -o "${OUT_DIR}/boss4x" "${SRC_BOSS4XCLI}"
go build -i ${FLAG} -v -o "${OUT_DIR}/evmxgoboss4x" "${SRC_EVMXGOBOSS4XCLI}"

cp ../../../../omnilink.para.toml "${OUT_DIR}"
cp ../../cross2eth/ebrelayer/relayer.toml "${OUT_DIR}/relayer.toml"
cp ./build/* "${OUT_DIR}"
cp ./build/abi/* "${OUT_DIR}"
cp ../../cross2eth/cmd/build/public/* "${OUT_DIR}"
cp ../../cross2eth/cmd/build/abi/* "${OUT_DIR}"
cp ../../cross2eth/boss4x/omnilink/deploy_omnilink.toml "${OUT_DIR}"
cp ../../cross2eth/boss4x/ethereum/deploy_ethereum.toml "${OUT_DIR}"

OUT_TESTDIR="${1}/dapptest/$strapp"
mkdir -p "${OUT_TESTDIR}"
cp ./test/* "${OUT_TESTDIR}"
