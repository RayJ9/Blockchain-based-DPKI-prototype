// Copyright Fuzamei Corp. 2018 All Rights Reserved.
// Use of this source code is governed by a BSD-style
// license that can be found in the LICENSE file.

package rpc_test

//only load all plugin and system
import (
	"testing"

	rpctypes "code.corp.bcollie.net/omnilink/omnilink-base/rpc/types"
	_ "code.corp.bcollie.net/omnilink/omnilink-base/system"
	"code.corp.bcollie.net/omnilink/omnilink-base/types"
	"code.corp.bcollie.net/omnilink/omnilink-base/util/testnode"
	_ "code.corp.bcollie.net/omnilink/omnilink-plugin/plugin"
	ty "code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/ticket/types"
	"github.com/stretchr/testify/assert"
)

func TestNewTicket(t *testing.T) {
	//选票(可以用hotwallet 关闭选票)
	cfg := types.NewOmnilinkConfig(types.GetDefaultCfgstring())
	cfg.GetModuleConfig().Consensus.Name = "ticket"
	mocker := testnode.NewWithConfig(cfg, nil)
	mocker.Listen()
	defer mocker.Close()

	in := &ty.TicketClose{MinerAddress: mocker.GetHotAddress()}
	var res rpctypes.ReplyHashes
	err := mocker.GetJSONC().Call("ticket.CloseTickets", in, &res)
	assert.Nil(t, err)
}
