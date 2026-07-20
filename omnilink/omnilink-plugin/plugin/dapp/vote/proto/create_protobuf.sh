#!/bin/bash
# proto生成命令，将pb.go文件生成到types/目录下, omnilink_path支持引用omnilink框架的proto文件
omnilink_path=$(go list -f '{{.Dir}}' "code.corp.bcollie.net/omnilink/omnilink-base")
protoc --go_out=plugins=grpc:../types ./*.proto --proto_path=. --proto_path="${omnilink_path}/types/proto/"
