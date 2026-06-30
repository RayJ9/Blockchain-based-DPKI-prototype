// Copyright Fuzamei Corp. 2018 All Rights Reserved.
// Use of this source code is governed by a BSD-style
// license that can be found in the LICENSE file.

package unfreeze

import (
	"code.corp.bcollie.net/omnilink/omnilink-base/pluginmgr"
	_ "code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/unfreeze/autotest" // register autotest package
	"code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/unfreeze/commands"
	"code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/unfreeze/executor"
	"code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/unfreeze/rpc"
	uf "code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/unfreeze/types"
)

func init() {
	pluginmgr.Register(&pluginmgr.PluginBase{
		Name:     uf.PackageName,
		ExecName: executor.GetName(),
		Exec:     executor.Init,
		Cmd:      commands.Cmd,
		RPC:      rpc.Init,
	})
}
