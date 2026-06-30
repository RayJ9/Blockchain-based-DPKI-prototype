// Copyright Fuzamei Corp. 2018 All Rights Reserved.
// Use of this source code is governed by a BSD-style
// license that can be found in the LICENSE file.

package relayd

import (
	"testing"

	"code.corp.bcollie.net/omnilink/omnilink-base/common"
	"code.corp.bcollie.net/omnilink/omnilink-base/common/address"
	"code.corp.bcollie.net/omnilink/omnilink-base/common/crypto"
	"code.corp.bcollie.net/omnilink/omnilink-base/types"
	typesmocks "code.corp.bcollie.net/omnilink/omnilink-base/types/mocks"
	types2 "code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/relay/types"
	"github.com/stretchr/testify/mock"
)

func TestGeneratePrivateKey(t *testing.T) {
	cr, err := crypto.Load(types.GetSignName("", types.SECP256K1), -1)
	if err != nil {
		t.Fatal(err)
	}

	key, err := cr.GenKey()
	if err != nil {
		t.Fatal(err)
	}

	t.Log("private key: ", common.ToHex(key.Bytes()))
	t.Log("publick key: ", common.ToHex(key.PubKey().Bytes()))
	t.Log("    address: ", address.PubKeyToAddr(address.DefaultID, key.PubKey().Bytes()))
}

func TestDealOrder(t *testing.T) {
	grpcClient := &typesmocks.OmnilinkClient{}
	relayd := &Relayd{}
	relayd.client33 = &Client33{}
	relayd.client33.OmnilinkClient = grpcClient
	relayd.btcClient = &btcdClient{
		connConfig:          nil,
		chainParams:         mainNetParams.Params,
		reconnectAttempts:   3,
		enqueueNotification: make(chan interface{}),
		dequeueNotification: make(chan interface{}),
		currentBlock:        make(chan *blockStamp),
		quit:                make(chan struct{}),
	}

	relayorder := &types2.RelayOrder{Id: string("id"), XTxHash: "hash"}
	rst := &types2.QueryRelayOrderResult{Orders: []*types2.RelayOrder{relayorder}}
	reply := &types.Reply{}
	reply.Msg = types.Encode(rst)
	grpcClient.On("QueryChain", mock.Anything, mock.Anything).Return(reply, nil).Once()
	grpcClient.On("SendTransaction", mock.Anything, mock.Anything).Return(nil, nil).Once()
	relayd.dealOrder()
}
