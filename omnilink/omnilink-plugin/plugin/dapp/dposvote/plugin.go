// Copyright Fuzamei Corp. 2018 All Rights Reserved.
// Use of this source code is governed by a BSD-style
// license that can be found in the LICENSE file.

package dposvote

import (
	"code.corp.bcollie.net/omnilink/omnilink-base/pluginmgr"
	"code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/dposvote/commands"
	"code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/dposvote/executor"
	"code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/dposvote/types"
)

func init() {
	pluginmgr.Register(&pluginmgr.PluginBase{
		Name:     types.DPosX,
		ExecName: executor.GetName(),
		Exec:     executor.Init,
		Cmd:      commands.DPosCmd,
	})
}
