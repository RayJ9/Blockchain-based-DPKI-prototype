// Copyright Fuzamei Corp. 2018 All Rights Reserved.
// Use of this source code is governed by a BSD-style
// license that can be found in the LICENSE file.

// Package coins 系统级coins dapp插件
package coinsx

import (
	"code.corp.bcollie.net/omnilink/omnilink-base/pluginmgr"
	"code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/coinsx/commands"

	"code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/coinsx/executor"
	"code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/coinsx/types"
)

func init() {
	pluginmgr.Register(&pluginmgr.PluginBase{
		Name:     types.CoinsxX,
		ExecName: executor.GetName(),
		Exec:     executor.Init,
		Cmd:      commands.CoinsxCmd,
		RPC:      nil,
	})
}
