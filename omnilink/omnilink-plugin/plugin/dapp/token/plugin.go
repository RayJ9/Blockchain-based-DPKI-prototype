// Copyright Fuzamei Corp. 2018 All Rights Reserved.
// Use of this source code is governed by a BSD-style
// license that can be found in the LICENSE file.

// Package token 创建token
package token

import (
	"code.corp.bcollie.net/omnilink/omnilink-base/pluginmgr"
	_ "code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/token/autotest" // register token autotest package
	"code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/token/commands"
	"code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/token/executor"
	"code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/token/rpc"
	"code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/token/types"
)

func init() {
	pluginmgr.Register(&pluginmgr.PluginBase{
		Name:     types.TokenX,
		ExecName: executor.GetName(),
		Exec:     executor.Init,
		Cmd:      commands.TokenCmd,
		RPC:      rpc.Init,
	})
}
