// Copyright Fuzamei Corp. 2018 All Rights Reserved.
// Use of this source code is governed by a BSD-style
// license that can be found in the LICENSE file.

// +build go1.8

package main

import (
	_ "code.corp.bcollie.net/omnilink/omnilink-base/system"
	"code.corp.bcollie.net/omnilink/omnilink-plugin/cli/buildflags"
	_ "code.corp.bcollie.net/omnilink/omnilink-plugin/plugin"

	"code.corp.bcollie.net/omnilink/omnilink-base/util/cli"
)

func main() {
	if buildflags.RPCAddr == "" {
		buildflags.RPCAddr = "http://localhost:8801"
	}
	cli.Run(buildflags.RPCAddr, buildflags.ParaName, "")
}
