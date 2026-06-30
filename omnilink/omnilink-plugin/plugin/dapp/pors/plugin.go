// Copyright Fuzamei Corp. 2018 All Rights Reserved.
// Use of this source code is governed by a BSD-style
// license that can be found in the LICENSE file.

package pors

import (
	"code.corp.bcollie.net/omnilink/omnilink-base/pluginmgr"
	"code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/pors/commands"
	"code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/pors/executor"
	"code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/pors/rpc"
	"code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/pors/types"
)

func init() {
	pluginmgr.Register(&pluginmgr.PluginBase{
		Name:     types.PorsX,
		ExecName: executor.GetName(),
		Exec:     executor.Init,
		Cmd:      commands.ValCmd,
		RPC:      rpc.Init,
	})
}
