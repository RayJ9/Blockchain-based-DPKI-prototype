// Copyright Fuzamei Corp. 2018 All Rights Reserved.
// Use of this source code is governed by a BSD-style
// license that can be found in the LICENSE file.

package hashlock

import (
	"code.corp.bcollie.net/omnilink/omnilink-base/pluginmgr"
	"code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/hashlock/commands"
	"code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/hashlock/executor"
	"code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/hashlock/types"
)

func init() {
	pluginmgr.Register(&pluginmgr.PluginBase{
		Name:     types.HashlockX,
		ExecName: executor.GetName(),
		Exec:     executor.Init,
		Cmd:      commands.HashlockCmd,
		RPC:      nil,
	})
}
