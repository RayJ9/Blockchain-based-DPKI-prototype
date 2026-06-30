#!/bin/sh

omnilink_path=$(go list -f '{{.Dir}}' "code.corp.bcollie.net/omnilink/omnilink-base")
protoc --go_out=plugins=grpc:../types ./*.proto --proto_path=. --proto_path="${omnilink_path}/types/proto/"
