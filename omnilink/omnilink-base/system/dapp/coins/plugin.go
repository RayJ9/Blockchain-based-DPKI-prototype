// Copyright Fuzamei Corp. 2018 All Rights Reserved.
// Use of this source code is governed by a BSD-style
// license that can be found in the LICENSE file.

// Package coins 系统级coins dapp插件
package coins

import (
	"code.corp.bcollie.net/omnilink/omnilink-base/pluginmgr"
	_ "code.corp.bcollie.net/omnilink/omnilink-base/system/dapp/coins/autotest" // register package
	"code.corp.bcollie.net/omnilink/omnilink-base/system/dapp/coins/executor"
	"code.corp.bcollie.net/omnilink/omnilink-base/system/dapp/coins/types"
)

func init() {
	pluginmgr.Register(&pluginmgr.PluginBase{
		Name:     types.CoinsX,
		ExecName: executor.GetName(),
		Exec:     executor.Init,
		Cmd:      nil,
		RPC:      nil,
	})
}
