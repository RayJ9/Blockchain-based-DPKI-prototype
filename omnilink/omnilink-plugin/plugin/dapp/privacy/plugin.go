// Copyright Fuzamei Corp. 2018 All Rights Reserved.
// Use of this source code is governed by a BSD-style
// license that can be found in the LICENSE file.

package privacy

import (
	"code.corp.bcollie.net/omnilink/omnilink-base/pluginmgr"
	_ "code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/privacy/autotest" // register autotest package
	"code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/privacy/commands"
	_ "code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/privacy/crypto" // register crypto package
	"code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/privacy/executor"
	"code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/privacy/rpc"
	"code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/privacy/types"
	_ "code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/privacy/wallet" // register wallet package
)

func init() {
	pluginmgr.Register(&pluginmgr.PluginBase{
		Name:     types.PrivacyX,
		ExecName: executor.GetName(),
		Exec:     executor.Init,
		Cmd:      commands.PrivacyCmd,
		RPC:      rpc.Init,
	})
}
