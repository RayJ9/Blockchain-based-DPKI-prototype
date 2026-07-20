#!/bin/sh
protoc --go_out=plugins=grpc:../types ./*.proto --proto_path=. --proto_path="$GOPATH/src/code.corp.bcollie.net/omnilink/omnilink-base/types/proto/"
