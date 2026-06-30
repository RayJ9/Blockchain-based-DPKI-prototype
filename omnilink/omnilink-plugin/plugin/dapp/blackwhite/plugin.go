// Copyright Fuzamei Corp. 2018 All Rights Reserved.
// Use of this source code is governed by a BSD-style
// license that can be found in the LICENSE file.

// Package blackwhite 黑白配游戏插件
package blackwhite

import (
	"code.corp.bcollie.net/omnilink/omnilink-base/pluginmgr"
	"code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/blackwhite/commands"
	"code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/blackwhite/executor"
	"code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/blackwhite/rpc"
	"code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/blackwhite/types"
)

func init() {
	pluginmgr.Register(&pluginmgr.PluginBase{
		Name:     types.BlackwhiteX,
		ExecName: executor.GetName(),
		Exec:     executor.Init,
		Cmd:      commands.BlackwhiteCmd,
		RPC:      rpc.Init,
	})
}
