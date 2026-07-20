// Copyright Fuzamei Corp. 2018 All Rights Reserved.
// Use of this source code is governed by a BSD-style
// license that can be found in the LICENSE file.

package rpc_test

import (
	"strings"
	"testing"

	commonlog "code.corp.bcollie.net/omnilink/omnilink-base/common/log"
	"code.corp.bcollie.net/omnilink/omnilink-base/rpc/jsonclient"
	rpctypes "code.corp.bcollie.net/omnilink/omnilink-base/rpc/types"
	"code.corp.bcollie.net/omnilink/omnilink-base/types"
	"code.corp.bcollie.net/omnilink/omnilink-base/util/testnode"
	pty "code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/relay/types"
	"github.com/stretchr/testify/assert"

	_ "code.corp.bcollie.net/omnilink/omnilink-base/system"
	_ "code.corp.bcollie.net/omnilink/omnilink-plugin/plugin"
)

func init() {
	commonlog.SetLogLevel("error")
}

func TestJRPCChannel(t *testing.T) {
	// 启动RPCmocker
	mocker := testnode.New("--notset--", nil)
	defer func() {
		mocker.Close()
	}()
	mocker.Listen()

	jrpcClient := mocker.GetJSONC()
	assert.NotNil(t, jrpcClient)

	testCases := []struct {
		fn func(*testing.T, *jsonclient.JSONClient) error
	}{
		{fn: testShowOnesCreateRelayOrdersCmd},
		{fn: testShowOnesAcceptRelayOrdersCmd},
		{fn: testShowOnesStatusOrdersCmd},
		{fn: testShowBTCHeadHeightListCmd},
		{fn: testGetBTCHeaderCurHeight},
	}
	for index, testCase := range testCases {
		err := testCase.fn(t, jrpcClient)
		if err == nil {
			continue
		}
		assert.NotEqualf(t, err, types.ErrActionNotSupport, "test index %d", index)
		if strings.Contains(err.Error(), "rpc: can't find") {
			assert.FailNowf(t, err.Error(), "test index %d", index)
		}
	}
}

func testShowOnesCreateRelayOrdersCmd(t *testing.T, jrpc *jsonclient.JSONClient) error {
	var rep interface{}
	var params rpctypes.Query4Jrpc
	req := &pty.ReqRelayAddrCoins{}
	params.Execer = "relay"
	params.FuncName = "GetSellRelayOrder"
	params.Payload = types.MustPBToJSON(req)
	rep = &pty.ReplyRelayOrders{}
	return jrpc.Call("Omnilink.Query", params, rep)
}

func testShowOnesAcceptRelayOrdersCmd(t *testing.T, jrpc *jsonclient.JSONClient) error {
	var rep interface{}
	var params rpctypes.Query4Jrpc
	req := &pty.ReqRelayAddrCoins{}
	params.Execer = "relay"
	params.FuncName = "GetBuyRelayOrder"
	params.Payload = types.MustPBToJSON(req)
	rep = &pty.ReplyRelayOrders{}
	return jrpc.Call("Omnilink.Query", params, rep)
}

func testShowOnesStatusOrdersCmd(t *testing.T, jrpc *jsonclient.JSONClient) error {
	var rep interface{}
	var params rpctypes.Query4Jrpc
	req := &pty.ReqRelayAddrCoins{}
	params.Execer = "relay"
	params.FuncName = "GetRelayOrderByStatus"
	params.Payload = types.MustPBToJSON(req)
	rep = &pty.ReplyRelayOrders{}
	return jrpc.Call("Omnilink.Query", params, rep)
}

func testShowBTCHeadHeightListCmd(t *testing.T, jrpc *jsonclient.JSONClient) error {
	var rep interface{}
	var params rpctypes.Query4Jrpc
	req := &pty.ReqRelayBtcHeaderHeightList{}
	params.Execer = "relay"
	params.FuncName = "GetBTCHeaderList"
	params.Payload = types.MustPBToJSON(req)
	rep = &pty.ReplyRelayBtcHeadHeightList{}
	return jrpc.Call("Omnilink.Query", params, rep)
}

func testGetBTCHeaderCurHeight(t *testing.T, jrpc *jsonclient.JSONClient) error {
	var params rpctypes.Query4Jrpc
	req := &pty.ReqRelayBtcHeaderHeightList{}
	js, err := types.PBToJSON(req)
	assert.Nil(t, err)
	params.Execer = "relay"
	params.FuncName = "GetBTCHeaderCurHeight"
	params.Payload = js
	rep := &pty.ReplayRelayQryBTCHeadHeight{}
	err = jrpc.Call("Omnilink.Query", params, rep)
	if err != nil {
		return err
	}
	assert.Equal(t, int64(-1), rep.CurHeight)
	return nil
}
