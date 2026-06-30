/*
 * Copyright Fuzamei Corp. 2018 All Rights Reserved.
 * Use of this source code is governed by a BSD-style
 * license that can be found in the LICENSE file.
 */

package oracle

import (
	"code.corp.bcollie.net/omnilink/omnilink-base/pluginmgr"
	"code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/oracle/commands"
	"code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/oracle/executor"
	"code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/oracle/types"
)

func init() {
	pluginmgr.Register(&pluginmgr.PluginBase{
		Name:     types.OracleX,
		ExecName: executor.GetName(),
		Exec:     executor.Init,
		Cmd:      commands.OracleCmd,
		//RPC:      rpc.Init,
	})
}
