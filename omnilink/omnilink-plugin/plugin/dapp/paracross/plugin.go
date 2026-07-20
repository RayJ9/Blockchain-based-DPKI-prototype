// Copyright Fuzamei Corp. 2018 All Rights Reserved.
// Use of this source code is governed by a BSD-style
// license that can be found in the LICENSE file.

package paracross

import (
	"code.corp.bcollie.net/omnilink/omnilink-base/pluginmgr"
	_ "code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/crypto/bls"              // register bls package for ut usage
	_ "code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/paracross/autotest" // register autotest package
	"code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/paracross/commands"
	"code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/paracross/executor"
	"code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/paracross/rpc"
	"code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/paracross/types"
	_ "code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/paracross/wallet" // register wallet package
)

func init() {
	pluginmgr.Register(&pluginmgr.PluginBase{
		Name:     types.ParaX,
		ExecName: executor.GetName(),
		Exec:     executor.Init,
		Cmd:      commands.ParcCmd,
		RPC:      rpc.Init,
	})
}
