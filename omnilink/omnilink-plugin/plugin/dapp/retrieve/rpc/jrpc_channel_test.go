// Copyright Fuzamei Corp. 2018 All Rights Reserved.
// Use of this source code is governed by a BSD-style
// license that can be found in the LICENSE file.

package rpc_test

import (
	"strings"
	"testing"

	"code.corp.bcollie.net/omnilink/omnilink-base/common"

	commonlog "code.corp.bcollie.net/omnilink/omnilink-base/common/log"
	"code.corp.bcollie.net/omnilink/omnilink-base/rpc/jsonclient"
	rpctypes "code.corp.bcollie.net/omnilink/omnilink-base/rpc/types"
	"code.corp.bcollie.net/omnilink/omnilink-base/types"
	"code.corp.bcollie.net/omnilink/omnilink-base/util/testnode"

	"code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/retrieve/rpc"
	pty "code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/retrieve/types"
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

	testCases := []struct {
		fn func(*testing.T, *jsonclient.JSONClient) error
	}{
		{fn: testBackupCmd},
		{fn: testPrepareCmd},
		{fn: testPerformCmd},
		{fn: testCancelCmd},
		{fn: testRetrieveQueryCmd},
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

func testBackupCmd(t *testing.T, jrpc *jsonclient.JSONClient) error {
	params := rpc.RetrieveBackupTx{}
	return jrpc.Call("retrieve.CreateRawRetrieveBackupTx", params, nil)
}

func testPrepareCmd(t *testing.T, jrpc *jsonclient.JSONClient) error {
	params := rpc.RetrievePrepareTx{}
	return jrpc.Call("retrieve.CreateRawRetrievePrepareTx", params, nil)
}

func testPerformCmd(t *testing.T, jrpc *jsonclient.JSONClient) error {
	params := rpc.RetrievePerformTx{
		BackupAddr:  "b",
		DefaultAddr: "d",
		Assets:      []rpc.Asset{{"e", "s"}},
	}

	var txS string
	t.Log("tx info", "x", params.Assets)
	err := jrpc.Call("retrieve.CreateRawRetrievePerformTx", &params, &txS)
	assert.Nil(t, err)
	var tx types.Transaction
	bytes, err := common.FromHex(txS)
	if err != nil {
		return err
	}
	err = types.Decode(bytes, &tx)
	if err != nil {
		return err
	}
	var p2 pty.RetrieveAction
	err = types.Decode(tx.Payload, &p2)
	t.Log("asset", p2.GetPerform().GetAssets())
	return err
}

func testCancelCmd(t *testing.T, jrpc *jsonclient.JSONClient) error {
	params := rpc.RetrieveCancelTx{}
	return jrpc.Call("retrieve.CreateRawRetrieveCancelTx", params, nil)
}

func testRetrieveQueryCmd(t *testing.T, jrpc *jsonclient.JSONClient) error {
	var rep interface{}
	var params rpctypes.Query4Jrpc
	req := &pty.ReqRetrieveInfo{}
	params.Execer = "retrieve"
	params.FuncName = "GetRetrieveInfo"
	params.Payload = types.MustPBToJSON(req)
	rep = &pty.RetrieveQuery{}
	return jrpc.Call("Omnilink.Query", params, rep)
}
