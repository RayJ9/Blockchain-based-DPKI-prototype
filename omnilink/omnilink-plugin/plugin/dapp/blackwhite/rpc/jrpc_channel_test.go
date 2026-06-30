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
	pty "code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/blackwhite/types"
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
		{fn: testCreateRawTxCmd},
		{fn: testPlayRawTxCmd},
		{fn: testShowRawTxCmd},
		{fn: testTimeoutDoneTxCmd},
		{fn: testRoundInfoCmd},
		{fn: testRoundListCmd},
		{fn: testLoopResultCmd},
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

func testCreateRawTxCmd(t *testing.T, jrpc *jsonclient.JSONClient) error {
	params := &pty.BlackwhiteCreateTxReq{}
	var res string
	return jrpc.Call("blackwhite.BlackwhiteCreateTx", params, &res)
}

func testPlayRawTxCmd(t *testing.T, jrpc *jsonclient.JSONClient) error {
	params := &pty.BlackwhitePlayTxReq{}
	var res string
	return jrpc.Call("blackwhite.BlackwhitePlayTx", params, &res)
}

func testShowRawTxCmd(t *testing.T, jrpc *jsonclient.JSONClient) error {
	params := &pty.BlackwhiteShowTxReq{}
	var res string
	return jrpc.Call("blackwhite.BlackwhiteShowTx", params, &res)
}

func testTimeoutDoneTxCmd(t *testing.T, jrpc *jsonclient.JSONClient) error {
	params := &pty.BlackwhiteTimeoutDoneTxReq{}
	var res string
	return jrpc.Call("blackwhite.BlackwhiteTimeoutDoneTx", params, &res)
}

func testRoundInfoCmd(t *testing.T, jrpc *jsonclient.JSONClient) error {
	var rep interface{}
	var params rpctypes.Query4Jrpc
	req := &pty.ReqBlackwhiteRoundInfo{}
	params.FuncName = pty.GetBlackwhiteRoundInfo
	params.Payload = types.MustPBToJSON(req)
	rep = &pty.ReplyBlackwhiteRoundInfo{}
	return jrpc.Call("Omnilink.Query", params, rep)
}

func testRoundListCmd(t *testing.T, jrpc *jsonclient.JSONClient) error {
	var rep interface{}
	var params rpctypes.Query4Jrpc
	req := &pty.ReqBlackwhiteRoundList{}
	params.FuncName = pty.GetBlackwhiteByStatusAndAddr
	params.Payload = types.MustPBToJSON(req)
	rep = &pty.ReplyBlackwhiteRoundList{}

	return jrpc.Call("Omnilink.Query", params, rep)
}

func testLoopResultCmd(t *testing.T, jrpc *jsonclient.JSONClient) error {
	var rep interface{}
	var params rpctypes.Query4Jrpc
	req := &pty.ReqLoopResult{}
	params.FuncName = pty.GetBlackwhiteloopResult
	params.Payload = types.MustPBToJSON(req)
	rep = &pty.ReplyLoopResults{}

	return jrpc.Call("Omnilink.Query", params, rep)
}
